"""
Visualiser for the agent failure taxonomy.

Usage:
    python visualise.py              # ASCII tree + severity table
    python visualise.py --mermaid    # output Mermaid mindmap
    python visualise.py --stats      # severity breakdown only
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml

SEVERITY_ORDER = ["critical", "high", "medium", "low"]
SEVERITY_ICON = {"critical": "[!]", "high": "[H]", "medium": "[M]", "low": "[L]"}


def load_taxonomy(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


def iter_failures(taxonomy: dict):
    """Yield (category, failure) pairs for every failure in the taxonomy."""
    for cat in taxonomy.get("categories", []):
        for failure in cat.get("failures", []):
            yield cat, failure


def print_tree(taxonomy: dict) -> None:
    print(f"Agent Failure Taxonomy  v{taxonomy.get('version', '?')}")
    print("=" * 60)
    categories = taxonomy.get("categories", [])
    for ci, cat in enumerate(categories):
        connector = "+" if ci < len(categories) - 1 else "+"
        print(f"{connector}-- {cat['label']}")
        failures = cat.get("failures", [])
        for fi, f in enumerate(failures):
            is_last = fi == len(failures) - 1
            branch = "   +" if not is_last else "   +"
            icon = SEVERITY_ICON.get(f.get("severity", ""), "   ")
            print(f"{branch}-- {icon} {f['label']}")
            print(f"   |     {f['description']}")
        print("   |")
    print()


def print_stats(taxonomy: dict) -> None:
    severity_counts: Counter = Counter()
    category_counts: Counter = Counter()

    for cat, f in iter_failures(taxonomy):
        sev = f.get("severity", "unknown")
        severity_counts[sev] += 1
        category_counts[cat["label"]] += 1

    total = sum(severity_counts.values())
    print(f"Total failure modes: {total}")
    print()

    print("By severity:")
    for sev in SEVERITY_ORDER:
        count = severity_counts.get(sev, 0)
        bar = "#" * count
        print(f"  {sev:<10} {count:>3}  {bar}")
    print()

    print("By category:")
    for label, count in category_counts.most_common():
        bar = "#" * count
        print(f"  {label:<30} {count:>3}  {bar}")
    print()


def print_mermaid(taxonomy: dict) -> None:
    print("```mermaid")
    print("mindmap")
    print("  root((Agent Failures))")
    for cat in taxonomy.get("categories", []):
        # indent with 4 spaces for category
        print(f"    {cat['label']}")
        for f in cat.get("failures", []):
            sev = f.get("severity", "")
            print(f"      {f['label']} [{sev}]")
    print("```")


def main() -> int:
    parser = argparse.ArgumentParser(description="Visualise the agent failure taxonomy.")
    parser.add_argument("--mermaid", action="store_true", help="Output as Mermaid mindmap")
    parser.add_argument("--stats", action="store_true", help="Show severity/category stats only")
    parser.add_argument(
        "--taxonomy",
        default=Path(__file__).parent / "taxonomy.yaml",
        type=Path,
        help="Path to taxonomy YAML (default: taxonomy.yaml in the same directory)",
    )
    args = parser.parse_args()

    taxonomy = load_taxonomy(args.taxonomy)

    if args.mermaid:
        print_mermaid(taxonomy)
    elif args.stats:
        print_stats(taxonomy)
    else:
        print_tree(taxonomy)
        print_stats(taxonomy)

    return 0


if __name__ == "__main__":
    sys.exit(main())
