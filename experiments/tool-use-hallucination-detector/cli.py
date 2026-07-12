"""
CLI for the tool-use hallucination detector.

Usage:
  python cli.py transcript.json
  python cli.py transcript.json --json
  python cli.py transcript.json --quiet   # exit 1 if issues found, no output
"""

import argparse
import json
import sys
from pathlib import Path

from detector import detect


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flag inconsistent tool chains in agent transcripts."
    )
    parser.add_argument("transcript", help="Path to a JSON transcript file")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")
    parser.add_argument("--quiet", "-q", action="store_true", help="Silent mode; exit 1 on issues")
    args = parser.parse_args()

    try:
        data = json.loads(Path(args.transcript).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error reading transcript: {exc}", file=sys.stderr)
        sys.exit(2)

    issues = detect(data)

    if not args.quiet:
        if args.as_json:
            print(
                json.dumps(
                    [{"step": i.step, "tool": i.tool, "path": i.path, "reason": i.reason} for i in issues],
                    indent=2,
                )
            )
        elif not issues:
            print("No inconsistencies found.")
        else:
            print(f"Found {len(issues)} inconsistency/ies:")
            for issue in issues:
                print(f"  {issue}")

    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
