# tool-use-hallucination-detector

Flag inconsistent tool chains in agent transcripts - for example, when an agent
reads a file it never wrote, or deletes a file that does not exist.

## What it detects

| Rule | Example |
|------|---------|
| Read before write | `read_file("out.txt")` with no prior `write_file` for that path |
| Read after delete | `delete_file("f.txt")` then `read_file("f.txt")` |
| Append before create | `append_file("log.txt")` with no prior write |
| Delete non-existent | `delete_file("ghost.py")` with no prior write |
| Double delete | deleting the same path twice |
| Move non-existent source | `move_file(src="a.txt", dst="b.txt")` with no prior write of `a.txt` |

Pre-existing files (files already on disk before the session) can be declared so
they do not trigger false positives.

## How to run

```bash
pip install -r requirements.txt

# Human-readable output
python cli.py sample_transcript.json

# JSON output (pipe-friendly)
python cli.py sample_transcript.json --json

# Silent mode - exit code 1 if issues found, 0 if clean
python cli.py sample_transcript.json --quiet

# Run tests
pytest test_detector.py -v
```

## Transcript formats

### Simple format

```json
{
  "pre_existing_files": ["README.md"],
  "steps": [
    {"id": 1, "tool": "write_file", "args": {"path": "out.txt"}},
    {"id": 2, "tool": "read_file",  "args": {"path": "out.txt"}},
    {"id": 3, "tool": "read_file",  "args": {"path": "never_written.txt"}}
  ]
}
```

### Anthropic API message format

The detector also accepts the raw messages array from the Anthropic API (with
`role: "assistant"` blocks containing `tool_use` content blocks).

```json
{
  "pre_existing_files": ["config.yaml"],
  "messages": [
    {
      "role": "assistant",
      "content": [
        {"type": "tool_use", "name": "read_file", "input": {"path": "config.yaml"}},
        {"type": "tool_use", "name": "write_file", "input": {"path": "report.md"}}
      ]
    }
  ]
}
```

## Findings

The heuristic catches the most common class of agent hallucination around
file I/O: the agent describes an action it did not actually take. In practice
these show up as "phantom reads" (reading a file the agent claimed to have
written but the write call never occurred) and "phantom deletes" (deleting
something that was never created, typically because the agent confused paths).

The tool is purely static - it traces the claimed sequence of tool calls and
checks internal consistency. It cannot catch hallucinations where the agent
invokes a real write but with wrong content, or where the underlying tool
silently fails.

## Scope

- Detects: internal inconsistencies in file-operation tool chains.
- Does not detect: semantic errors, wrong arguments, or cross-tool data
  dependencies (e.g., using the output of one tool as the input to another).
- Does not execute any tool calls or require access to the actual filesystem.

## Out of scope

- Network operations (HTTP, database) - no consistent read/write semantics.
- Process execution chains.
- Detecting whether tool results were faithfully used by the model.
