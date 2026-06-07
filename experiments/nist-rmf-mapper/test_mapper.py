"""Tests for nist-rmf-mapper."""

import tempfile
from pathlib import Path

import pytest

from mapper import detect_artifacts, load_rmf, map_artifacts, render_report


def test_detect_tests_by_prefix():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "test_accuracy.py").write_text("def test_acc(): assert True")
        arts = detect_artifacts(p)
        assert any("test_accuracy.py" in f for f in arts["tests"])


def test_detect_tests_in_subdir():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "tests").mkdir()
        (p / "tests" / "check.py").write_text("# placeholder")
        arts = detect_artifacts(p)
        assert any("tests/check.py" in f for f in arts["tests"])


def test_detect_model_card():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "model_card.md").write_text("# Model Card\nModel: my-model")
        arts = detect_artifacts(p)
        assert len(arts["model_card"]) == 1


def test_measure_categories_covered_by_tests():
    rmf = load_rmf()
    arts = {
        "tests": ["tests/test_model.py"],
        "logs": [],
        "model_card": [],
        "docs": [],
        "policy": [],
        "audit": [],
        "eval": [],
    }
    mapping = map_artifacts(arts, rmf)
    measure_cats = {k: v for k, v in mapping.items() if k.startswith("MEASURE")}
    covered = [v for v in measure_cats.values() if v["artifacts"]]
    assert len(covered) >= 1, "At least one MEASURE category should have test evidence"


def test_render_report_structure():
    rmf = load_rmf()
    arts = {
        "tests": ["test_model.py"],
        "model_card": ["model_card.md"],
        "logs": ["monitor.py"],
        "docs": ["README.md"],
        "policy": ["config/governance_policy.yaml"],
        "audit": ["audit_log.json"],
        "eval": ["evaluate.py"],
    }
    mapping = map_artifacts(arts, rmf)
    report = render_report(mapping, arts)
    assert "NIST AI RMF" in report
    assert "GOV" in report
    assert "MEASURE" in report
    assert "MANAGE" in report
    assert "Coverage:" in report
    assert "yes" in report
