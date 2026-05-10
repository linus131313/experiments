"""Tests for agent-trajectory-viz."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from viz import detect_format, parse_claude, parse_openai, render_mermaid

CLAUDE_DATA = {
    "messages": [
        {"role": "user", "content": "Read foo.txt"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Reading now."},
                {"type": "tool_use", "id": "tu_1", "name": "read_file", "input": {"path": "foo.txt"}},
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "tu_1", "content": "hello world"},
            ],
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": "The file says: hello world"}],
        },
    ]
}

OPENAI_DATA = {
    "messages": [
        {"role": "user", "content": "Search for logs."},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "tc_1",
                    "type": "function",
                    "function": {"name": "search", "arguments": '{"query": "logs"}'},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "tc_1", "content": "found 3 log files"},
        {"role": "assistant", "content": "Found 3 log files."},
    ]
}


class TestDetectFormat(unittest.TestCase):
    def test_detects_claude(self):
        self.assertEqual(detect_format(CLAUDE_DATA), 'claude')

    def test_detects_openai(self):
        self.assertEqual(detect_format(OPENAI_DATA), 'openai')

    def test_empty_defaults_to_claude(self):
        self.assertEqual(detect_format({"messages": []}), 'claude')


class TestParseEvents(unittest.TestCase):
    def test_claude_event_types(self):
        events = parse_claude(CLAUDE_DATA)
        types = [e['type'] for e in events]
        self.assertIn('message', types)
        self.assertIn('tool_call', types)
        self.assertIn('tool_result', types)

    def test_claude_tool_name(self):
        events = parse_claude(CLAUDE_DATA)
        calls = [e for e in events if e['type'] == 'tool_call']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['name'], 'read_file')

    def test_openai_event_types(self):
        events = parse_openai(OPENAI_DATA)
        types = [e['type'] for e in events]
        self.assertIn('message', types)
        self.assertIn('tool_call', types)
        self.assertIn('tool_result', types)

    def test_openai_tool_name(self):
        events = parse_openai(OPENAI_DATA)
        calls = [e for e in events if e['type'] == 'tool_call']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['name'], 'search')


class TestRenderMermaid(unittest.TestCase):
    def _diagram(self, data, fmt='claude'):
        events = parse_claude(data) if fmt == 'claude' else parse_openai(data)
        return render_mermaid(events)

    def test_starts_with_sequenceDiagram(self):
        diagram = self._diagram(CLAUDE_DATA)
        self.assertTrue(diagram.startswith('sequenceDiagram'))

    def test_contains_participant_lines(self):
        diagram = self._diagram(CLAUDE_DATA)
        self.assertIn('participant User', diagram)
        self.assertIn('participant Assistant', diagram)
        self.assertIn('participant read_file', diagram)

    def test_openai_diagram_has_tool(self):
        diagram = self._diagram(OPENAI_DATA, fmt='openai')
        self.assertIn('participant search', diagram)

    def test_example_files_roundtrip(self):
        base = Path(__file__).parent
        for fname, fmt in [('example_claude.json', 'claude'), ('example_openai.json', 'openai')]:
            with open(base / fname) as f:
                data = json.load(f)
            events = parse_claude(data) if fmt == 'claude' else parse_openai(data)
            diagram = render_mermaid(events)
            self.assertIn('sequenceDiagram', diagram)
            self.assertGreater(diagram.count('\n'), 3)


if __name__ == '__main__':
    unittest.main()
