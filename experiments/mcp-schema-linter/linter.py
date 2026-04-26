#!/usr/bin/env python3
"""MCP schema linter - check tool definitions for common mistakes."""

import json
import re
import sys
import argparse
from dataclasses import dataclass
from typing import Any


VAGUE_NAMES = {
    "data", "input", "output", "value", "result", "info",
    "obj", "item", "thing", "stuff", "content", "payload",
    "params", "args", "kwargs", "x", "y", "z", "n", "s",
    "text", "body", "msg", "message", "response", "request",
}

TOOL_NAME_RE = re.compile(r'^[a-z][a-z0-9_]*$')
PARAM_NAME_RE = re.compile(r'^[a-z][a-z0-9_]*$')


@dataclass
class Issue:
    severity: str   # ERROR or WARNING
    rule: str
    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.severity:7}  [{self.rule}] {self.location}: {self.message}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Issue):
            return NotImplemented
        return (self.severity, self.rule, self.location, self.message) == (
            other.severity, other.rule, other.location, other.message
        )


def _lint_param(name: str, schema: Any, loc: str) -> list[Issue]:
    issues: list[Issue] = []

    if not isinstance(schema, dict):
        issues.append(Issue("ERROR", "invalid-param-schema", loc,
                            "Parameter schema must be a JSON object."))
        return issues

    if len(name) == 1 or name.lower() in VAGUE_NAMES:
        issues.append(Issue("WARNING", "param-unclear-name", loc,
                            f"Parameter name '{name}' is vague; use a descriptive name."))
    elif not PARAM_NAME_RE.match(name):
        issues.append(Issue("WARNING", "param-name-style", loc,
                            f"Parameter name '{name}' should be lowercase snake_case."))

    desc = schema.get("description", "")
    if not desc:
        issues.append(Issue("ERROR", "param-missing-description", f"{loc}.description",
                            f"Parameter '{name}' has no description."))
    elif len(desc.strip()) < 10:
        issues.append(Issue("WARNING", "param-description-too-short", f"{loc}.description",
                            f"Description for '{name}' is only {len(desc.strip())} chars; add more detail."))

    ptype = schema.get("type")
    if ptype == "object" and "properties" not in schema and "additionalProperties" not in schema:
        issues.append(Issue("WARNING", "param-over-broad-object", loc,
                            f"Parameter '{name}' typed as 'object' with no properties or "
                            "additionalProperties; tighten the schema or document the shape."))
    if ptype == "array" and "items" not in schema:
        issues.append(Issue("WARNING", "param-over-broad-array", loc,
                            f"Parameter '{name}' typed as 'array' with no items schema."))

    return issues


def _lint_input_schema(schema: Any, loc: str) -> list[Issue]:
    issues: list[Issue] = []

    if not isinstance(schema, dict):
        issues.append(Issue("ERROR", "invalid-input-schema", loc,
                            "inputSchema must be a JSON object."))
        return issues

    if schema.get("type") != "object":
        issues.append(Issue("WARNING", "input-schema-not-object", loc,
                            f"inputSchema.type should be 'object', got '{schema.get('type')}'."))

    props = schema.get("properties", {})
    if not isinstance(props, dict):
        issues.append(Issue("ERROR", "invalid-properties", f"{loc}.properties",
                            "'properties' must be a JSON object."))
        return issues

    for param_name, param_schema in props.items():
        issues.extend(_lint_param(param_name, param_schema,
                                  f"{loc}.properties.{param_name}"))
    return issues


def _lint_tool(tool: Any, index: int) -> list[Issue]:
    issues: list[Issue] = []
    loc = f"tools[{index}]"

    if not isinstance(tool, dict):
        issues.append(Issue("ERROR", "invalid-tool", loc, "Tool must be a JSON object."))
        return issues

    name = tool.get("name", "")
    if not name:
        issues.append(Issue("ERROR", "tool-name-missing", f"{loc}.name",
                            "Tool has no name."))
    elif not TOOL_NAME_RE.match(name):
        issues.append(Issue("WARNING", "tool-name-style", f"{loc}.name",
                            f"Tool name '{name}' should be lowercase snake_case "
                            "(letters, digits, underscores; start with a letter)."))

    desc = tool.get("description", "")
    if not desc:
        issues.append(Issue("ERROR", "tool-missing-description", f"{loc}.description",
                            "Tool has no description."))
    elif len(desc.strip()) < 10:
        issues.append(Issue("WARNING", "tool-description-too-short", f"{loc}.description",
                            f"Tool description is only {len(desc.strip())} chars; add more context."))

    input_schema = tool.get("inputSchema")
    if input_schema is None:
        issues.append(Issue("ERROR", "tool-missing-input-schema", f"{loc}.inputSchema",
                            "Tool has no inputSchema."))
    else:
        issues.extend(_lint_input_schema(input_schema, f"{loc}.inputSchema"))

    return issues


def lint(schema: Any) -> list[Issue]:
    """Lint an MCP tools schema dict and return all issues found."""
    if not isinstance(schema, dict):
        return [Issue("ERROR", "invalid-root", "$",
                      "Root value must be a JSON object.")]
    tools = schema.get("tools")
    if tools is None:
        return [Issue("ERROR", "missing-tools-key", "$",
                      "Root object has no 'tools' key.")]
    if not isinstance(tools, list):
        return [Issue("ERROR", "tools-not-array", "$.tools",
                      "'tools' must be a JSON array.")]
    issues: list[Issue] = []
    for i, tool in enumerate(tools):
        issues.extend(_lint_tool(tool, i))
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lint an MCP server tools schema JSON file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exit codes: 0 = clean, 1 = issues found, 2 = usage/parse error.",
    )
    parser.add_argument("file", help="Path to MCP tools JSON file.")
    parser.add_argument("--fail-on-warning", action="store_true",
                        help="Exit 1 if warnings are found (default: only errors).")
    args = parser.parse_args()

    try:
        with open(args.file) as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON - {e}", file=sys.stderr)
        sys.exit(2)

    issues = lint(schema)
    if not issues:
        print("No issues found.")
        sys.exit(0)

    for issue in issues:
        print(issue)

    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) in "
          f"{len(schema.get('tools', []))} tool(s).")

    if errors or (args.fail_on_warning and warnings):
        sys.exit(1)


if __name__ == "__main__":
    main()
