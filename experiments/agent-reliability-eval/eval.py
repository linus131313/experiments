"""Tiny eval framework for agent reliability patterns.

Patterns covered: naive, retry, fallback, grounded, retry+fallback.
Uses a configurable mock tool with no external dependencies.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Core data types
# ---------------------------------------------------------------------------


@dataclass
class ToolCall:
    success: bool
    value: Any
    latency_ms: float


@dataclass
class PatternResult:
    success: bool
    value: Any
    calls: int
    total_latency_ms: float


# ---------------------------------------------------------------------------
# Mock tool
# ---------------------------------------------------------------------------


class MockTool:
    """Simulates a flaky tool with configurable failure and format-error rates."""

    def __init__(
        self,
        name: str,
        success_rate: float,
        latency_ms: float,
        format_error_rate: float = 0.0,
        seed: int = 42,
    ):
        self.name = name
        self.success_rate = success_rate
        self.latency_ms = latency_ms
        self.format_error_rate = format_error_rate
        self._rng = random.Random(seed)

    def call(self, query: str) -> ToolCall:
        if self._rng.random() >= self.success_rate:
            return ToolCall(False, None, self.latency_ms)
        if self._rng.random() < self.format_error_rate:
            # Tool "succeeds" at the API level but returns a malformed response.
            return ToolCall(True, {"raw": query}, self.latency_ms)
        return ToolCall(True, f"answer:{query}", self.latency_ms)


# ---------------------------------------------------------------------------
# Reliability patterns
# ---------------------------------------------------------------------------


def naive(primary: MockTool, query: str) -> PatternResult:
    """Single attempt; accept any non-error result."""
    tc = primary.call(query)
    return PatternResult(tc.success, tc.value, 1, tc.latency_ms)


def retry(
    primary: MockTool,
    query: str,
    max_attempts: int = 3,
    backoff_ms: float = 50.0,
) -> PatternResult:
    """Retry on tool failure with exponential backoff."""
    calls, total_ms = 0, 0.0
    for i in range(max_attempts):
        tc = primary.call(query)
        calls += 1
        total_ms += tc.latency_ms
        if tc.success:
            return PatternResult(True, tc.value, calls, total_ms)
        if i < max_attempts - 1:
            total_ms += backoff_ms * (2**i)
    return PatternResult(False, None, calls, total_ms)


def fallback(primary: MockTool, secondary: MockTool, query: str) -> PatternResult:
    """Try primary; fall back to secondary on failure."""
    tc = primary.call(query)
    calls, total_ms = 1, tc.latency_ms
    if tc.success:
        return PatternResult(True, tc.value, calls, total_ms)
    tc2 = secondary.call(query)
    return PatternResult(tc2.success, tc2.value, calls + 1, total_ms + tc2.latency_ms)


def grounded(
    primary: MockTool,
    validator: Callable[[Any], bool],
    query: str,
) -> PatternResult:
    """Validate tool output; reject results that fail the schema check."""
    tc = primary.call(query)
    if not tc.success:
        return PatternResult(False, None, 1, tc.latency_ms)
    if validator(tc.value):
        return PatternResult(True, tc.value, 1, tc.latency_ms)
    return PatternResult(False, None, 1, tc.latency_ms)


def retry_with_fallback(
    primary: MockTool,
    secondary: MockTool,
    query: str,
    max_primary: int = 2,
) -> PatternResult:
    """Retry primary up to max_primary times, then try secondary once."""
    r = retry(primary, query, max_attempts=max_primary)
    if r.success:
        return r
    tc = secondary.call(query)
    return PatternResult(
        tc.success, tc.value, r.calls + 1, r.total_latency_ms + tc.latency_ms
    )


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------

QUERIES = [
    "capital of France",
    "speed of light",
    "boiling point H2O",
    "first prime number",
    "Euler's number",
]


def _is_valid(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("answer:")


@dataclass
class EvalMetrics:
    pattern: str
    success_rate: float
    avg_calls: float
    avg_latency_ms: float


def _run(name: str, fn: Callable[[str], PatternResult], n: int = 500) -> EvalMetrics:
    ok = calls = 0
    ms = 0.0
    total = n * len(QUERIES)
    for query in QUERIES:
        for _ in range(n):
            r = fn(query)
            if r.success:
                ok += 1
            calls += r.calls
            ms += r.total_latency_ms
    return EvalMetrics(name, ok / total, calls / total, ms / total)


def _tools(seed: int = 42) -> tuple[MockTool, MockTool]:
    primary = MockTool(
        "primary",
        success_rate=0.60,
        latency_ms=100.0,
        format_error_rate=0.10,
        seed=seed,
    )
    secondary = MockTool(
        "secondary",
        success_rate=0.85,
        latency_ms=250.0,
        format_error_rate=0.02,
        seed=seed + 1,
    )
    return primary, secondary


def main() -> None:
    seed = 42
    results: list[EvalMetrics] = []

    p, s = _tools(seed)
    results.append(_run("naive", lambda q: naive(p, q)))

    p, s = _tools(seed)
    results.append(_run("retry(3)", lambda q: retry(p, q, max_attempts=3)))

    p, s = _tools(seed)
    results.append(_run("fallback", lambda q: fallback(p, s, q)))

    p, s = _tools(seed)
    results.append(
        _run("retry(2)+fallback", lambda q: retry_with_fallback(p, s, q, max_primary=2))
    )

    p, s = _tools(seed)
    results.append(_run("grounded", lambda q: grounded(p, _is_valid, q)))

    print(f"\n{'Pattern':<22} {'Success%':>9} {'Avg calls':>10} {'Avg ms':>8}")
    print("-" * 55)
    for r in results:
        print(
            f"{r.pattern:<22} {r.success_rate * 100:>8.1f}%"
            f" {r.avg_calls:>10.2f} {r.avg_latency_ms:>8.1f}"
        )
    print()


if __name__ == "__main__":
    main()
