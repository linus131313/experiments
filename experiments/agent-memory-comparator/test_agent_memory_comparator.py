"""Tests for the agent-memory-comparator experiment."""

import pytest

from backends import GraphBackend, KVBackend, VectorBackend
from metrics import context_chars, mean_metrics, precision_at_k, recall_at_k
from workload import CORPUS, QUERIES


def _all_backends():
    backends = [VectorBackend(), GraphBackend(), KVBackend()]
    for b in backends:
        b.build(CORPUS)
    return backends


def test_backends_return_k_or_fewer_results():
    for b in _all_backends():
        results = b.query("Python memory management", k=3)
        assert 0 < len(results) <= 3


def test_all_results_are_valid_corpus_ids():
    for b in _all_backends():
        for doc_id in b.query("Java threading concurrency", k=5):
            assert doc_id in CORPUS, f"Unknown doc id: {doc_id}"


def test_precision_at_k():
    assert precision_at_k(["a", "b"], ["a", "c"]) == pytest.approx(0.5)
    assert precision_at_k([], ["a"]) == pytest.approx(0.0)
    assert precision_at_k(["a", "b"], ["a", "b"]) == pytest.approx(1.0)


def test_recall_at_k():
    assert recall_at_k(["a"], ["a", "b"]) == pytest.approx(0.5)
    assert recall_at_k([], ["a"]) == pytest.approx(0.0)
    assert recall_at_k(["a", "b", "c"], ["a", "b"]) == pytest.approx(1.0)


def test_mean_metrics_shape_and_bounds():
    b = VectorBackend()
    b.build(CORPUS)
    m = mean_metrics(b, QUERIES, CORPUS, k=3)
    assert set(m) == {"precision_at_k", "recall_at_k", "mean_context_chars"}
    assert 0.0 <= m["precision_at_k"] <= 1.0
    assert 0.0 <= m["recall_at_k"] <= 1.0
    assert m["mean_context_chars"] > 0
