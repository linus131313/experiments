"""Tests for the MCP schema linter."""

import pytest
from linter import lint, Issue


def _rules(issues: list[Issue]) -> set[str]:
    return {i.rule for i in issues}


def test_valid_schema_produces_no_issues():
    schema = {
        "tools": [
            {
                "name": "read_file",
                "description": "Read the full contents of a file from disk.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Absolute path to the file to read.",
                        },
                        "encoding": {
                            "type": "string",
                            "description": "Character encoding to use, defaults to utf-8.",
                        },
                    },
                    "required": ["file_path"],
                },
            }
        ]
    }
    assert lint(schema) == []


def test_missing_tool_description_is_error():
    schema = {
        "tools": [
            {
                "name": "do_something",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]
    }
    assert "tool-missing-description" in _rules(lint(schema))


def test_param_missing_description_is_error():
    schema = {
        "tools": [
            {
                "name": "my_tool",
                "description": "Does something useful with the given file.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                    },
                },
            }
        ]
    }
    assert "param-missing-description" in _rules(lint(schema))


def test_vague_param_name_is_warning():
    schema = {
        "tools": [
            {
                "name": "process_record",
                "description": "Processes the given record against stored rules.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "The record payload to process.",
                        }
                    },
                },
            }
        ]
    }
    issues = lint(schema)
    assert "param-unclear-name" in _rules(issues)
    assert all(i.severity == "WARNING" for i in issues if i.rule == "param-unclear-name")


def test_over_broad_object_param_is_warning():
    schema = {
        "tools": [
            {
                "name": "call_api",
                "description": "Makes an HTTP request to the configured endpoint.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "request_body": {
                            "type": "object",
                            "description": "The JSON body to send with the request.",
                        }
                    },
                },
            }
        ]
    }
    assert "param-over-broad-object" in _rules(lint(schema))


def test_tool_name_style_warning_for_camel_case():
    schema = {
        "tools": [
            {
                "name": "ReadFile",
                "description": "Reads the contents of a file on the filesystem.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read from disk.",
                        }
                    },
                },
            }
        ]
    }
    assert "tool-name-style" in _rules(lint(schema))
