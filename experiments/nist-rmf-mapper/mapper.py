#!/usr/bin/env python3
"""Map code artifacts in a project directory to NIST AI RMF categories."""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

import yaml


def load_rmf() -> dict:
    data_path = Path(__file__).parent / "rmf_data.yaml"
    with open(data_path) as f:
        return yaml.safe_load(f)


def detect_artifacts(project_dir: Path) -> Dict[str, List[str]]:
    """Scan a project directory and classify files by artifact type."""
    artifacts: Dict[str, List[str]] = {
        "tests": [],
        "logs": [],
        "model_card": [],
        "docs": [],
        "policy": [],
        "audit": [],
        "eval": [],
    }

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for fname in files:
            fpath = Path(root) / fname
            try:
                rel = str(fpath.relative_to(project_dir))
            except ValueError:
                continue

            name_lower = fname.lower()
            rel_lower = rel.lower()

            # Tests
            in_test_dir = (
                "/tests/" in rel_lower
                or rel_lower.startswith("tests/")
                or "/test/" in rel_lower
                or rel_lower.startswith("test/")
            )
            if (
                re.match(r"test_|.+_test\.", name_lower)
                or in_test_dir
                or name_lower.endswith("_spec.py")
                or name_lower.endswith("_spec.js")
                or name_lower.endswith("_spec.ts")
            ):
                artifacts["tests"].append(rel)

            # Model card
            if "model_card" in name_lower or "modelcard" in name_lower:
                artifacts["model_card"].append(rel)

            # Audit
            if "audit" in name_lower:
                artifacts["audit"].append(rel)

            # Docs (README, CONTRIBUTING, CHANGELOG, or anything in docs/)
            if name_lower in ("readme.md", "readme.txt", "contributing.md", "changelog.md"):
                artifacts["docs"].append(rel)
            elif "/docs/" in rel_lower or rel_lower.startswith("docs/"):
                artifacts["docs"].append(rel)

            # Policy/governance
            if "policy" in name_lower or "governance" in name_lower:
                artifacts["policy"].append(rel)
            elif "/policies/" in rel_lower or rel_lower.startswith("policies/"):
                artifacts["policy"].append(rel)

            # Evaluations/benchmarks
            if (
                re.search(r"eval|benchmark|metrics", name_lower)
                and not name_lower.startswith("test_")
            ):
                artifacts["eval"].append(rel)

            # Logging (Python files that import logging or use a logger)
            if name_lower.endswith(".py") and rel not in artifacts["eval"]:
                try:
                    text = fpath.read_text(errors="ignore")
                    if "import logging" in text or "getLogger" in text:
                        artifacts["logs"].append(rel)
                except OSError:
                    pass

    return artifacts


def map_artifacts(
    artifacts: Dict[str, List[str]], rmf: dict
) -> Dict[str, dict]:
    """Match artifacts to each NIST AI RMF category."""
    mapping: Dict[str, dict] = {}
    for fn_name, fn_data in rmf["functions"].items():
        for cat in fn_data["categories"]:
            cat_id = cat["id"]
            matched: List[str] = []
            for art_type in cat["artifact_types"]:
                matched.extend(artifacts.get(art_type, []))
            # Deduplicate while preserving order
            seen: set = set()
            deduped = [x for x in matched if not (x in seen or seen.add(x))]
            mapping[cat_id] = {
                "name": cat["name"],
                "function": fn_name,
                "artifact_types": cat["artifact_types"],
                "artifacts": deduped,
            }
    return mapping


def render_report(mapping: Dict[str, dict], artifacts: Dict[str, List[str]]) -> str:
    lines = ["# NIST AI RMF Artifact Mapping Report\n"]

    total = len(mapping)
    covered = sum(1 for v in mapping.values() if v["artifacts"])
    lines.append(f"**Coverage: {covered}/{total} categories have at least one artifact.**\n")

    # Summary table
    lines.append("## Summary\n")
    lines.append("| ID | Name | Evidence | Artifact Types |")
    lines.append("|---|---|:---:|---|")
    for cat_id, data in mapping.items():
        status = "yes" if data["artifacts"] else "no"
        types = ", ".join(data["artifact_types"])
        lines.append(f"| {cat_id} | {data['name']} | {status} | {types} |")
    lines.append("")

    # Detail by function
    lines.append("## Detail by Function\n")
    current_fn = None
    for cat_id, data in mapping.items():
        if data["function"] != current_fn:
            current_fn = data["function"]
            lines.append(f"### {current_fn}\n")
        lines.append(f"#### {cat_id}: {data['name']}\n")
        lines.append(f"*Supported by: {', '.join(data['artifact_types'])}*\n")
        if data["artifacts"]:
            lines.append("Matched artifacts:")
            for f in data["artifacts"][:6]:
                lines.append(f"- `{f}`")
        else:
            lines.append("*No artifacts found - consider adding evidence.*")
        lines.append("")

    # Artifact inventory
    lines.append("## Artifact Inventory\n")
    any_found = False
    for art_type, files in artifacts.items():
        if files:
            any_found = True
            lines.append(f"**{art_type}** ({len(files)} file(s))")
            for f in files[:6]:
                lines.append(f"- `{f}`")
            lines.append("")
    if not any_found:
        lines.append("*No artifacts detected. Make sure the path points to a project.*\n")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map project artifacts to NIST AI RMF categories."
    )
    parser.add_argument("project_dir", help="Path to the project directory to scan")
    parser.add_argument(
        "-o", "--output", help="Write report to this file instead of stdout"
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        print(f"Error: '{project_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    rmf = load_rmf()
    artifacts = detect_artifacts(project_dir)
    mapping = map_artifacts(artifacts, rmf)
    report = render_report(mapping, artifacts)

    if args.output:
        Path(args.output).write_text(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
