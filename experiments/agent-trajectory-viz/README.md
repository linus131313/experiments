# agent-trajectory-viz

Parse a Claude or OpenAI agent transcript and render the tool-call trajectory as a [Mermaid](https://mermaid.js.org/) sequence diagram.

## What it does

Reads a JSON transcript (Claude API format or OpenAI Chat Completions format), extracts the sequence of user messages, assistant turns, tool calls, and tool results, then emits a `sequenceDiagram` block that can be dropped into any Mermaid renderer or GitHub Markdown.

Auto-detects format by inspecting the message structure. Pass `--format` to override.

## How to run

```bash
# Claude-format transcript
python viz.py example_claude.json

# OpenAI-format transcript
python viz.py example_openai.json

# Write to file
python viz.py example_claude.json -o trajectory.mmd

# Force format
python viz.py my_trace.json --format openai
```

No dependencies beyond Python 3.10+.

## Example output

Running on `example_openai.json`:

```
sequenceDiagram
    participant User
    participant Assistant
    participant search_files
    participant count_lines
    User->>Assistant: Find all Python files and count lines in each.
    Assistant->>+search_files: pattern=*.py, root=.
    search_files-->>-Assistant: ['main.py', 'utils.py', 'test_suite.py']
    Assistant->>+count_lines: path=main.py
    count_lines-->>-Assistant: 142
    ...
```

Paste into the [Mermaid live editor](https://mermaid.live) or a GitHub Markdown block to see the rendered diagram.

## Running tests

```bash
python -m unittest test_viz -v
```

## Findings

- A simple event-list representation (message / tool_call / tool_result) decouples parsing from rendering cleanly.
- Labels are truncated at 60 characters so diagrams remain readable even with large JSON args.
- The `+` / `-` activation syntax in Mermaid gives visual call depth, which makes parallel or nested tool calls immediately obvious.

## Scope

Handles flat (non-streaming) transcript JSON. Both Claude multi-block content and OpenAI `tool_calls` arrays are supported.

## Out of scope

- Streaming JSONL transcripts (chunks would need reassembly).
- LangChain / LangSmith trace formats.
- HTML or SVG output (Mermaid rendering is left to the viewer's toolchain).
- Nested sub-agent transcripts.
