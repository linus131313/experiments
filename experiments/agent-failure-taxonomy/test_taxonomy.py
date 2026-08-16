"""Tests for the agent-failure-taxonomy experiment."""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

TAXONOMY_PATH = Path(__file__).parent / "taxonomy.yaml"
VALID_SEVERITIES = {"critical", "high", "medium", "low"}
REQUIRED_FAILURE_FIELDS = {"id", "label", "severity", "description", "signals", "mitigations"}
REQUIRED_CATEGORY_FIELDS = {"id", "label", "description", "failures"}


def load() -> dict:
    with TAXONOMY_PATH.open() as f:
        return yaml.safe_load(f)


def test_taxonomy_loads():
    data = load()
    assert isinstance(data, dict)
    assert "categories" in data
    assert len(data["categories"]) > 0


def test_all_required_fields_present():
    data = load()
    for cat in data["categories"]:
        missing_cat = REQUIRED_CATEGORY_FIELDS - cat.keys()
        assert not missing_cat, f"Category {cat.get('id')} missing fields: {missing_cat}"
        for f in cat.get("failures", []):
            missing = REQUIRED_FAILURE_FIELDS - f.keys()
            assert not missing, f"Failure {f.get('id')} missing fields: {missing}"


def test_severities_are_valid():
    data = load()
    for cat in data["categories"]:
        for f in cat.get("failures", []):
            sev = f.get("severity")
            assert sev in VALID_SEVERITIES, (
                f"Failure '{f.get('id')}' has invalid severity '{sev}'"
            )


def test_failure_count_by_severity():
    data = load()
    counts = {s: 0 for s in VALID_SEVERITIES}
    for cat in data["categories"]:
        for f in cat.get("failures", []):
            counts[f["severity"]] += 1
    total = sum(counts.values())
    assert total >= 10, f"Expected at least 10 failure modes, got {total}"
    assert counts["critical"] >= 1, "Expected at least one critical failure"
    assert counts["high"] >= 3, "Expected at least three high-severity failures"


def test_visualiser_runs_and_produces_output():
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "visualise.py"), "--stats"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"visualise.py exited with {result.returncode}: {result.stderr}"
    assert "Total failure modes" in result.stdout
    assert len(result.stdout.strip()) > 50
