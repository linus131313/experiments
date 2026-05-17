"""Tests for reliability pattern implementations."""
import pytest

from eval import (
    MockTool,
    PatternResult,
    _is_valid,
    fallback,
    grounded,
    naive,
    retry,
    retry_with_fallback,
)

QUERY = "test query"


def always_ok(seed: int = 1) -> MockTool:
    return MockTool("ok", success_rate=1.0, latency_ms=10.0, seed=seed)


def always_fail(seed: int = 2) -> MockTool:
    return MockTool("fail", success_rate=0.0, latency_ms=10.0, seed=seed)


def test_naive_success():
    r = naive(always_ok(), QUERY)
    assert r.success
    assert r.calls == 1
    assert r.total_latency_ms == 10.0


def test_naive_failure():
    r = naive(always_fail(), QUERY)
    assert not r.success
    assert r.calls == 1


def test_retry_exhausts_on_constant_failure():
    r = retry(always_fail(), QUERY, max_attempts=3)
    assert not r.success
    assert r.calls == 3


def test_fallback_uses_secondary_when_primary_fails():
    r = fallback(always_fail(), always_ok(), QUERY)
    assert r.success
    assert r.calls == 2


def test_grounded_rejects_format_error():
    # format_error_rate=1.0 means the tool always returns a malformed dict
    bad = MockTool("bad", success_rate=1.0, latency_ms=10.0, format_error_rate=1.0, seed=1)
    r = grounded(bad, _is_valid, QUERY)
    assert not r.success
