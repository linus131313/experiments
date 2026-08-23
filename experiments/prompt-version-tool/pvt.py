#!/usr/bin/env python3
"""pvt - Git-native prompt versioning with structural test cases."""

import argparse
import subprocess
import sys
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

PROMPTS_DIR = ".prompts"


def _git_root():
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(r.stdout.strip())
    except subprocess.CalledProcessError:
        return Path(".")


def _prompts_dir():
    return _git_root() / PROMPTS_DIR


# ---------------------------------------------------------------------------
# Test runner (pure, no subprocess - easy to unit test)
# ---------------------------------------------------------------------------

def run_test_case(test: dict, prompt_text: str) -> tuple[str, bool, str]:
    """Return (name, passed, reason)."""
    name = test.get("name", "unnamed")
    ttype = test.get("type", "")
    value = test.get("value")

    if ttype == "contains":
        ok = str(value) in prompt_text
        reason = "" if ok else f"'{value}' not found in prompt"
    elif ttype == "not_contains":
        ok = str(value) not in prompt_text
        reason = "" if ok else f"'{value}' found but should be absent"
    elif ttype == "max_chars":
        ok = len(prompt_text) <= int(value)
        reason = "" if ok else f"length {len(prompt_text)} > max {value}"
    elif ttype == "min_chars":
        ok = len(prompt_text) >= int(value)
        reason = "" if ok else f"length {len(prompt_text)} < min {value}"
    elif ttype == "starts_with":
        ok = prompt_text.lstrip().startswith(str(value))
        reason = "" if ok else f"prompt does not start with '{value}'"
    elif ttype == "regex":
        ok = bool(re.search(str(value), prompt_text, re.MULTILINE))
        reason = "" if ok else f"regex '{value}' did not match"
    elif ttype == "max_lines":
        lines = prompt_text.splitlines()
        ok = len(lines) <= int(value)
        reason = "" if ok else f"{len(lines)} lines > max {value}"
    else:
        ok = False
        reason = f"unknown test type '{ttype}'"

    return name, ok, reason


def run_tests(prompt_text: str, tests: list[dict]) -> list[tuple[str, bool, str]]:
    return [run_test_case(t, prompt_text) for t in tests]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(_args):
    pdir = _prompts_dir()
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / ".gitkeep").touch()
    print(f"Prompt store initialised at {pdir}")


def cmd_save(args):
    name = args.name
    pdir = _prompts_dir() / name
    pdir.mkdir(parents=True, exist_ok=True)

    prompt_file = pdir / "prompt.txt"

    if args.file:
        content = Path(args.file).read_text()
    else:
        print("Paste prompt then press Ctrl+D:", file=sys.stderr)
        content = sys.stdin.read()

    if not content.strip():
        print("Empty prompt - nothing saved.", file=sys.stderr)
        sys.exit(1)

    prompt_file.write_text(content)

    subprocess.run(["git", "add", str(prompt_file)], check=True)
    msg = args.message or f"prompt: update {name}"
    subprocess.run(["git", "commit", "-m", msg, "--", str(prompt_file)], check=True)
    print(f"Saved prompt '{name}'")


def cmd_log(args):
    prompt_file = _prompts_dir() / args.name / "prompt.txt"
    result = subprocess.run(
        ["git", "log", "--oneline", "--", str(prompt_file)],
        capture_output=True, text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    else:
        print(f"No history found for '{args.name}'")


def cmd_diff(args):
    prompt_file = _prompts_dir() / args.name / "prompt.txt"
    rev2 = args.rev2 if args.rev2 else "HEAD"
    result = subprocess.run(
        ["git", "diff", args.rev1, rev2, "--", str(prompt_file)],
        capture_output=True, text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    else:
        print("No differences found.")


def cmd_show(args):
    """Print the prompt text at an optional git revision."""
    prompt_file = _prompts_dir() / args.name / "prompt.txt"
    if args.rev:
        result = subprocess.run(
            ["git", "show", f"{args.rev}:{prompt_file}"],
            capture_output=True, text=True,
        )
        print(result.stdout, end="")
    else:
        if prompt_file.exists():
            print(prompt_file.read_text(), end="")
        else:
            print(f"No prompt found for '{args.name}'", file=sys.stderr)
            sys.exit(1)


def cmd_test(args):
    pdir = _prompts_dir() / args.name
    prompt_file = pdir / "prompt.txt"
    tests_file = pdir / "tests.yaml"

    if not prompt_file.exists():
        print(f"No prompt found for '{args.name}'", file=sys.stderr)
        sys.exit(1)
    if not tests_file.exists():
        print(f"No tests.yaml found for '{args.name}'", file=sys.stderr)
        sys.exit(1)

    prompt_text = prompt_file.read_text()
    raw = yaml.safe_load(tests_file.read_text())
    tests = raw.get("tests", [])

    results = run_tests(prompt_text, tests)
    passed = failed = 0
    for name, ok, reason in results:
        status = "PASS" if ok else "FAIL"
        line = f"  [{status}] {name}"
        if not ok:
            line += f"  ({reason})"
        print(line)
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)


def cmd_list(_args):
    pdir = _prompts_dir()
    if not pdir.exists():
        print("Prompt store not initialised. Run: pvt init")
        return
    prompts = sorted(p.name for p in pdir.iterdir() if p.is_dir())
    if prompts:
        for p in prompts:
            print(f"  {p}")
    else:
        print("No prompts saved yet.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="pvt",
        description="Git-native prompt versioning with test cases",
    )
    subs = parser.add_subparsers(dest="command", metavar="COMMAND")

    subs.add_parser("init", help="Initialise the prompt store in the current repo")

    save_p = subs.add_parser("save", help="Save a prompt (stdin or -f file)")
    save_p.add_argument("name", help="Prompt slug")
    save_p.add_argument("-f", "--file", help="Read prompt from file instead of stdin")
    save_p.add_argument("-m", "--message", help="Commit message")

    log_p = subs.add_parser("log", help="Show version history for a prompt")
    log_p.add_argument("name")

    diff_p = subs.add_parser("diff", help="Diff two revisions of a prompt")
    diff_p.add_argument("name")
    diff_p.add_argument("rev1")
    diff_p.add_argument("rev2", nargs="?", default=None)

    show_p = subs.add_parser("show", help="Print prompt text (optionally at a revision)")
    show_p.add_argument("name")
    show_p.add_argument("rev", nargs="?", default=None)

    test_p = subs.add_parser("test", help="Run structural test cases for a prompt")
    test_p.add_argument("name")

    subs.add_parser("list", help="List all saved prompts")

    args = parser.parse_args()
    dispatch = {
        "init": cmd_init,
        "save": cmd_save,
        "log": cmd_log,
        "diff": cmd_diff,
        "show": cmd_show,
        "test": cmd_test,
        "list": cmd_list,
    }
    if args.command in dispatch:
        dispatch[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
