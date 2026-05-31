#!/usr/bin/env python3
"""
ISO 42001 checklist generator.

Reads a YAML control spec and emits an auditor-friendly Markdown checklist.

Usage:
    python generator.py <controls.yaml> [-o output.md] [--clause CLAUSE]
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import yaml


def load_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    _validate_spec(data)
    return data


def _validate_spec(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML must be a mapping")
    if "sections" not in data:
        raise ValueError("YAML must contain a 'sections' key")
    for i, sec in enumerate(data["sections"]):
        if "clause" not in sec:
            raise ValueError(f"Section {i} missing 'clause'")
        if "title" not in sec:
            raise ValueError(f"Section {i} missing 'title'")
        controls = sec.get("controls", [])
        for j, ctrl in enumerate(controls):
            if "id" not in ctrl:
                raise ValueError(f"Section {i}, control {j} missing 'id'")
            if "title" not in ctrl:
                raise ValueError(f"Section {i}, control {j} missing 'title'")
            if "checks" not in ctrl or not ctrl["checks"]:
                raise ValueError(f"Control {ctrl.get('id')} has no checks")


def _check_text(check: object) -> str:
    if isinstance(check, str):
        return check
    if isinstance(check, dict):
        return check.get("text", "")
    return str(check)


def _check_hint(check: object) -> str:
    if isinstance(check, dict):
        return check.get("evidence_hint", "")
    return ""


def _escape_pipe(s: str) -> str:
    return s.replace("|", "\\|")


def render_control(ctrl: dict) -> str:
    lines = []
    cid = ctrl["id"]
    title = ctrl["title"]
    ref = ctrl.get("ref", "")
    desc = ctrl.get("description", "")

    lines.append(f"### {cid} - {title}\n")
    if ref:
        lines.append(f"*Reference: {ref}*\n")
    if desc:
        lines.append(f"{desc}\n")

    lines.append("| # | Check | Status | Evidence | Notes |")
    lines.append("|---|-------|--------|----------|-------|")

    for idx, check in enumerate(ctrl["checks"], start=1):
        text = _escape_pipe(_check_text(check))
        hint = _escape_pipe(_check_hint(check))
        lines.append(f"| {idx} | {text} | [ ] | {hint} | |")

    return "\n".join(lines)


def render_section(sec: dict) -> str:
    clause = sec["clause"]
    title = sec["title"]
    blocks = [f"## Clause {clause}: {title}\n"]
    for ctrl in sec.get("controls", []):
        blocks.append(render_control(ctrl))
    return "\n\n".join(blocks)


def render_toc(sections: list) -> str:
    lines = ["## Contents\n"]
    for sec in sections:
        clause = sec["clause"]
        title = sec["title"]
        anchor = f"clause-{clause}-{title.lower().replace(' ', '-').replace('/', '')}"
        lines.append(f"- [Clause {clause}: {title}](#{anchor})")
        for ctrl in sec.get("controls", []):
            cid = ctrl["id"]
            ctitle = ctrl["title"]
            ctrl_anchor = (
                f"{cid}---{ctitle.lower().replace(' ', '-').replace('/', '')}"
            )
            lines.append(f"  - [{cid} {ctitle}](#{ctrl_anchor})")
    return "\n".join(lines)


def generate(spec: dict, clause_filter: str | None = None) -> str:
    meta = spec.get("meta", {})
    standard = meta.get("standard", "ISO/IEC 42001:2023")
    title = meta.get("title", "AI Management System Checklist")
    scope = meta.get("scope", "")
    version = meta.get("version", "")

    sections = spec["sections"]
    if clause_filter:
        sections = [s for s in sections if str(s["clause"]) == str(clause_filter)]
        if not sections:
            raise ValueError(f"No section found for clause '{clause_filter}'")

    header_lines = [
        f"# {title}",
        "",
        f"**Standard:** {standard}  ",
        f"**Generated:** {date.today().isoformat()}  ",
    ]
    if version:
        header_lines.append(f"**Spec version:** {version}  ")
    if scope:
        header_lines.append(f"**Scope:** {scope}  ")
    header_lines += [
        "",
        "> Fill in **Status** (`[x]` pass / `[!]` finding / `[-]` N/A) and",
        "> **Evidence** (document name and section) during the audit walkthrough.",
    ]

    parts = ["\n".join(header_lines)]

    if not clause_filter:
        parts.append(render_toc(sections))

    for sec in sections:
        parts.append(render_section(sec))

    return "\n\n---\n\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate an ISO 42001 audit checklist from a YAML control spec"
    )
    parser.add_argument("spec", help="Path to the YAML control spec file")
    parser.add_argument(
        "-o", "--output", help="Output Markdown file (default: stdout)"
    )
    parser.add_argument(
        "--clause",
        metavar="CLAUSE",
        help="Emit only the section for this clause number (e.g. 8)",
    )
    args = parser.parse_args(argv)

    try:
        spec = load_spec(args.spec)
        md = generate(spec, clause_filter=args.clause)
    except (ValueError, yaml.YAMLError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(md, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
