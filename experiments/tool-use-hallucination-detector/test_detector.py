"""Tests for the tool-use hallucination detector."""

import pytest
from detector import detect, detect_from_steps, Inconsistency


# --- helpers ---

def steps(*ops):
    """Build a step list from (tool, path) pairs."""
    return [{"id": i + 1, "tool": tool, "args": {"path": path}} for i, (tool, path) in enumerate(ops)]


# --- core write/read rules ---

def test_clean_write_then_read():
    assert detect_from_steps(steps(("write_file", "out.txt"), ("read_file", "out.txt"))) == []


def test_read_before_write_flagged():
    issues = detect_from_steps(steps(("read_file", "ghost.txt")))
    assert len(issues) == 1
    assert "never created" in issues[0].reason
    assert issues[0].tool == "read_file"


def test_pre_existing_not_flagged():
    issues = detect_from_steps(steps(("read_file", "Makefile")), pre_existing={"Makefile"})
    assert issues == []


def test_read_after_delete_flagged():
    s = steps(("write_file", "tmp.txt"), ("delete_file", "tmp.txt"), ("read_file", "tmp.txt"))
    issues = detect_from_steps(s)
    assert len(issues) == 1
    assert "delete" in issues[0].reason


def test_append_before_create_flagged():
    issues = detect_from_steps(steps(("append_file", "log.txt")))
    assert len(issues) == 1
    assert "never created" in issues[0].reason


# --- delete rules ---

def test_delete_nonexistent_flagged():
    issues = detect_from_steps(steps(("delete_file", "phantom.txt")))
    assert len(issues) == 1
    assert "never created" in issues[0].reason


def test_double_delete_flagged():
    s = steps(("write_file", "x.txt"), ("delete_file", "x.txt"), ("delete_file", "x.txt"))
    issues = detect_from_steps(s)
    assert len(issues) == 1
    assert "twice" in issues[0].reason


# --- move rules ---

def test_move_nonexistent_flagged():
    s = [{"id": 1, "tool": "move_file", "args": {"path": "a.txt", "dst": "b.txt"}}]
    issues = detect_from_steps(s)
    assert len(issues) == 1
    assert "moved" in issues[0].reason


def test_move_then_read_dst_clean():
    s = [
        {"id": 1, "tool": "write_file", "args": {"path": "a.txt"}},
        {"id": 2, "tool": "move_file", "args": {"path": "a.txt", "dst": "b.txt"}},
        {"id": 3, "tool": "read_file", "args": {"path": "b.txt"}},
    ]
    assert detect_from_steps(s) == []


# --- Anthropic API message format ---

def test_claude_message_format_detects_hallucination():
    transcript = {
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "t1", "name": "write_file", "input": {"path": "a.txt"}},
                    {"type": "tool_use", "id": "t2", "name": "read_file", "input": {"path": "b.txt"}},
                ],
            }
        ]
    }
    issues = detect(transcript)
    assert len(issues) == 1
    assert issues[0].path == "b.txt"


def test_claude_message_format_clean():
    transcript = {
        "pre_existing_files": ["README.md"],
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "t1", "name": "read_file", "input": {"path": "README.md"}},
                    {"type": "tool_use", "id": "t2", "name": "write_file", "input": {"path": "out.txt"}},
                ],
            }
        ],
    }
    assert detect(transcript) == []


# --- flat list format ---

def test_flat_list_format():
    transcript = [
        {"id": 1, "tool": "write_file", "args": {"path": "f.txt"}},
        {"id": 2, "tool": "read_file", "args": {"path": "missing.txt"}},
    ]
    issues = detect(transcript)
    assert len(issues) == 1
    assert issues[0].path == "missing.txt"


# --- multi-issue transcript ---

def test_multiple_issues_reported():
    s = steps(
        ("read_file", "a.txt"),
        ("delete_file", "b.txt"),
        ("write_file", "c.txt"),
        ("read_file", "d.txt"),
    )
    issues = detect_from_steps(s)
    assert len(issues) == 3
    paths = {i.path for i in issues}
    assert paths == {"a.txt", "b.txt", "d.txt"}
