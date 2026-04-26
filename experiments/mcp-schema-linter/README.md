# mcp-schema-linter

A static linter for MCP (Model Context Protocol) server tool schemas. It reads
a JSON file containing a `tools` array and flags common authoring mistakes that
hurt agent reliability.

## What it checks

| Rule | Severity | Description |
|------|----------|-------------|
| `tool-name-missing` | ERROR | Tool has no name |
| `tool-name-style` | WARNING | Tool name is not lowercase snake_case |
| `tool-missing-description` | ERROR | Tool has no `description` field |
| `tool-description-too-short` | WARNING | Description is under 10 characters |
| `tool-missing-input-schema` | ERROR | Tool has no `inputSchema` |
| `input-schema-not-object` | WARNING | `inputSchema.type` is not `object` |
| `param-missing-description` | ERROR | A parameter has no `description` |
| `param-description-too-short` | WARNING | Parameter description is under 10 characters |
| `param-unclear-name` | WARNING | Parameter name is a single letter or a generic name like `data`, `input`, `value` |
| `param-name-style` | WARNING | Parameter name is not lowercase snake_case |
| `param-over-broad-object` | WARNING | Parameter typed `object` with no `properties` or `additionalProperties` |
| `param-over-broad-array` | WARNING | Parameter typed `array` with no `items` schema |

## Input format

A JSON file with a top-level `tools` array following the MCP tool definition
shape:

```json
{
  "tools": [
    {
      "name": "read_file",
      "description": "Read the full contents of a file from the local filesystem.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "file_path": {
            "type": "string",
            "description": "Absolute path to the file to read."
          }
        },
        "required": ["file_path"]
      }
    }
  ]
}
```

## How to run

```bash
# Lint a schema file (exits 0 if clean, 1 if issues found)
python linter.py path/to/tools.json

# Treat warnings as failures too
python linter.py --fail-on-warning path/to/tools.json

# Run against the included bad example
python linter.py example_bad.json
```

Example output:

```
WARNING  [tool-name-style] tools[1].name: Tool name 'SearchFiles' should be lowercase snake_case ...
ERROR    [tool-missing-description] tools[1].description: Tool has no description.
WARNING  [param-unclear-name] tools[1].inputSchema.properties.x: Parameter name 'x' is vague; use a descriptive name.
ERROR    [param-missing-description] tools[1].inputSchema.properties.x.description: Parameter 'x' has no description.
...

2 error(s), 6 warning(s) in 2 tool(s).
```

## Run tests

```bash
pip install -r requirements.txt
python -m pytest test_linter.py -v
```

## Findings

- Missing descriptions are the single most common mistake in public MCP server
  schemas. Agents rely on descriptions to decide when and how to call a tool;
  a blank description is functionally equivalent to a broken tool.
- Vague parameter names (`data`, `input`, `value`) correlate with over-broad
  types: authors often don't know what shape the value should be, so they skip
  both the name and the schema.
- The `object` without `properties` anti-pattern forces the model to guess the
  expected structure from the description alone, increasing hallucination risk.

## Scope

- Static analysis only - no network calls, no model inference.
- Reads MCP tool schemas serialised as JSON; YAML not supported.
- Does not validate JSON Schema correctness beyond a shallow structural check.

## Out of scope

- Semantic quality of descriptions (requires an LLM judge).
- Runtime schema conformance checking against actual tool responses.
- YAML input.
- Full JSON Schema Draft 7/2020-12 meta-schema validation.
