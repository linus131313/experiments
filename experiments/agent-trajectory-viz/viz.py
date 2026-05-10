#!/usr/bin/env python3
"""Parse Claude/OpenAI transcripts and render tool-call trajectories as Mermaid diagrams."""

import argparse
import json
import sys

TRUNCATE = 60


def _trunc(s: str, n: int = TRUNCATE) -> str:
    s = str(s).replace('"', "'").replace('\n', ' ')
    return s[:n] + '...' if len(s) > n else s


def _safe(name: str) -> str:
    return name.replace('-', '_').replace(' ', '_').replace(':', '_').replace('.', '_')


def detect_format(data: dict) -> str:
    """Return 'claude' or 'openai' based on transcript structure."""
    for msg in data.get('messages', []):
        content = msg.get('content', '')
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get('type') in ('tool_use', 'tool_result'):
                    return 'claude'
        if msg.get('role') == 'tool' or msg.get('tool_calls'):
            return 'openai'
    return 'claude'


def parse_claude(data: dict) -> list:
    """Extract events from a Claude-format transcript."""
    events = []
    for msg in data.get('messages', []):
        role = msg.get('role', '')
        content = msg.get('content', '')
        if isinstance(content, str):
            if content.strip():
                events.append({'type': 'message', 'role': role, 'text': content})
            continue
        if not isinstance(content, list):
            continue
        text_parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get('type')
            if btype == 'text':
                text_parts.append(block.get('text', ''))
            elif btype == 'tool_use':
                if text_parts:
                    events.append({'type': 'message', 'role': role, 'text': ' '.join(text_parts)})
                    text_parts = []
                events.append({
                    'type': 'tool_call',
                    'name': block.get('name', 'unknown'),
                    'id': block.get('id', ''),
                    'args': block.get('input', {}),
                })
            elif btype == 'tool_result':
                rc = block.get('content', '')
                if isinstance(rc, list):
                    rc = ' '.join(b.get('text', '') for b in rc if isinstance(b, dict))
                events.append({
                    'type': 'tool_result',
                    'tool_use_id': block.get('tool_use_id', ''),
                    'result': str(rc),
                })
        if text_parts:
            events.append({'type': 'message', 'role': role, 'text': ' '.join(text_parts)})
    return events


def parse_openai(data: dict) -> list:
    """Extract events from an OpenAI-format transcript."""
    events = []
    for msg in data.get('messages', []):
        role = msg.get('role', '')
        content = msg.get('content') or ''
        tool_calls = msg.get('tool_calls') or []
        if role == 'tool':
            events.append({
                'type': 'tool_result',
                'tool_use_id': msg.get('tool_call_id', ''),
                'result': str(content),
            })
            continue
        if isinstance(content, str) and content.strip():
            events.append({'type': 'message', 'role': role, 'text': content})
        for tc in tool_calls:
            fn = tc.get('function', {})
            raw_args = fn.get('arguments', '{}')
            try:
                args = json.loads(raw_args)
            except (json.JSONDecodeError, TypeError):
                args = raw_args
            events.append({
                'type': 'tool_call',
                'name': fn.get('name', 'unknown'),
                'id': tc.get('id', ''),
                'args': args,
            })
    return events


def render_mermaid(events: list) -> str:
    """Render events as a Mermaid sequenceDiagram string."""
    tools: list[str] = []
    tool_id_map: dict[str, str] = {}
    for e in events:
        if e['type'] == 'tool_call':
            name = _safe(e['name'])
            if name not in tools:
                tools.append(name)
            if e.get('id'):
                tool_id_map[e['id']] = name

    lines = ['sequenceDiagram']
    lines.append('    participant User')
    lines.append('    participant Assistant')
    for tool in tools:
        lines.append(f'    participant {tool}')

    last_tool: str | None = None
    for e in events:
        etype = e['type']
        if etype == 'message':
            text = _trunc(e['text'])
            if e['role'] == 'user':
                lines.append(f'    User->>Assistant: {text}')
            elif e['role'] == 'assistant':
                lines.append(f'    Assistant->>User: {text}')
        elif etype == 'tool_call':
            name = _safe(e['name'])
            last_tool = name
            args = e.get('args', {})
            if isinstance(args, dict) and args:
                label = ', '.join(f'{k}={v}' for k, v in list(args.items())[:3])
            elif isinstance(args, str) and args:
                label = args
            else:
                label = 'call'
            lines.append(f'    Assistant->>+{name}: {_trunc(label)}')
        elif etype == 'tool_result':
            tid = e.get('tool_use_id', '')
            name = tool_id_map.get(tid, last_tool or 'Tool')
            name = _safe(name)
            lines.append(f'    {name}-->>-Assistant: {_trunc(e["result"])}')

    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Render an agent transcript as a Mermaid sequence diagram'
    )
    parser.add_argument('transcript', help='Path to transcript JSON file')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument(
        '--format', choices=['claude', 'openai'],
        help='Transcript format (auto-detected if omitted)'
    )
    args = parser.parse_args()

    with open(args.transcript) as f:
        data = json.load(f)

    fmt = args.format or detect_format(data)
    events = parse_claude(data) if fmt == 'claude' else parse_openai(data)
    diagram = render_mermaid(events)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(diagram + '\n')
        print(f'Written to {args.output}', file=sys.stderr)
    else:
        print(diagram)


if __name__ == '__main__':
    main()
