"""
Tool-use hallucination detector for agent transcripts.

Detects inconsistent tool chains such as:
- reading a file the agent never wrote (and that is not pre-existing)
- deleting a file that was never created
- reading a file after it was deleted
- appending to a file that was never created
- moving a source file that does not exist
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FILE_READ_OPS = {"read_file", "read", "open_file", "cat", "get_file_contents"}
FILE_WRITE_OPS = {"write_file", "write", "create_file", "create", "touch", "put_file"}
FILE_APPEND_OPS = {"append_file", "append", "append_to_file"}
FILE_DELETE_OPS = {"delete_file", "delete", "remove_file", "remove", "unlink"}
FILE_MOVE_OPS = {"move_file", "move", "rename_file", "rename"}


@dataclass
class Inconsistency:
    step: int | str
    tool: str
    path: str
    reason: str

    def __str__(self) -> str:
        return f"Step {self.step} [{self.tool}] {self.path!r}: {self.reason}"


def _path_from_args(args: dict[str, Any]) -> str:
    for key in ("path", "file", "filename", "src", "source", "filepath"):
        if key in args:
            return str(args[key])
    return ""


def _dst_from_args(args: dict[str, Any]) -> str:
    for key in ("dst", "destination", "dest", "to", "target"):
        if key in args:
            return str(args[key])
    return ""


def detect_from_steps(
    steps: list[dict[str, Any]],
    pre_existing: set[str] | None = None,
) -> list[Inconsistency]:
    """Scan a flat list of tool-call steps and return any inconsistencies found."""
    known: set[str] = set(pre_existing or [])
    deleted: set[str] = set()
    issues: list[Inconsistency] = []

    for step in steps:
        sid = step.get("id", step.get("turn", "?"))
        tool = step.get("tool", "").lower()
        args: dict[str, Any] = step.get("args", step.get("input", {})) or {}
        path = _path_from_args(args)

        if tool in FILE_WRITE_OPS:
            if path:
                known.add(path)
                deleted.discard(path)

        elif tool in FILE_READ_OPS or tool in FILE_APPEND_OPS:
            if path:
                if path in deleted:
                    issues.append(Inconsistency(sid, tool, path, "read after delete"))
                elif path not in known:
                    issues.append(
                        Inconsistency(sid, tool, path, "read before write - never created in this trace")
                    )

        elif tool in FILE_DELETE_OPS:
            if path:
                if path in deleted:
                    issues.append(Inconsistency(sid, tool, path, "deleted twice"))
                elif path not in known:
                    issues.append(
                        Inconsistency(sid, tool, path, "deleted but never created in this trace")
                    )
                else:
                    deleted.add(path)
                    known.discard(path)

        elif tool in FILE_MOVE_OPS:
            dst = _dst_from_args(args)
            if path:
                if path not in known or path in deleted:
                    issues.append(
                        Inconsistency(sid, tool, path, "moved but source never created in this trace")
                    )
                else:
                    known.discard(path)
                    deleted.add(path)
                    if dst:
                        known.add(dst)

    return issues


def _flatten_claude_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Anthropic API message format into flat step dicts."""
    steps: list[dict[str, Any]] = []
    sid = 1
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", [])
        if isinstance(content, str):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                steps.append(
                    {"id": sid, "tool": block.get("name", ""), "args": block.get("input", {})}
                )
                sid += 1
    return steps


def detect(transcript: dict[str, Any] | list[dict[str, Any]]) -> list[Inconsistency]:
    """
    Detect hallucinations in a transcript.

    Accepts three shapes:
      - list of step dicts (flat format)
      - dict with "steps" key (simple format)
      - dict with "messages" key (Anthropic API format)

    In all cases a "pre_existing_files" list may be supplied to avoid
    false positives for files already on disk at session start.
    """
    if isinstance(transcript, list):
        return detect_from_steps(transcript)

    pre = set(transcript.get("pre_existing_files", []))

    if "messages" in transcript:
        steps = _flatten_claude_messages(transcript["messages"])
    else:
        steps = transcript.get("steps", [])

    return detect_from_steps(steps, pre)


def detect_file(path: str | Path) -> list[Inconsistency]:
    """Load a JSON transcript from disk and run detection."""
    data = json.loads(Path(path).read_text())
    return detect(data)
