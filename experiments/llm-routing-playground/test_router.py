"""Tests for the LLM routing playground."""

import pytest
from backends import FastCheapBackend, SlowExpensiveBackend
from router import Router, RouterConfig, Request


def make_req(**kw):
    defaults = dict(input_tokens=500, complexity=0.5, latency_budget_ms=5000, max_cost_usd=0.10)
    defaults.update(kw)
    return Request(**defaults)


def test_cost_strategy_picks_cheaper_backend():
    router = Router(RouterConfig(strategy="cost"))
    decision = router.route(make_req(input_tokens=500, complexity=0.5), seed=1)
    # fast-cheap is always cheaper at the same token count
    assert decision.chosen_backend == "fast-cheap"


def test_quality_strategy_picks_better_backend_for_complex_task():
    router = Router(RouterConfig(strategy="quality"))
    decision = router.route(make_req(complexity=0.9), seed=2)
    # slow-expensive has higher quality on complex tasks
    assert decision.chosen_backend == "slow-expensive"


def test_latency_strategy_picks_faster_backend():
    router = Router(RouterConfig(strategy="latency"))
    decision = router.route(make_req(input_tokens=100, complexity=0.3), seed=3)
    assert decision.chosen_backend == "fast-cheap"


def test_balanced_strategy_routes_simple_to_fast():
    router = Router(RouterConfig(strategy="balanced"))
    decision = router.route(make_req(complexity=0.1, input_tokens=200), seed=5)
    # For simple tasks the fast backend's quality is good enough and wins on cost+latency
    assert decision.chosen_backend == "fast-cheap"


def test_history_accumulates_across_calls():
    router = Router(RouterConfig(strategy="balanced"))
    for i in range(4):
        router.route(make_req(complexity=i * 0.3), seed=i)
    assert len(router.history) == 4


def test_budget_hard_limit_excludes_expensive_backend():
    # With a very tight cost cap and enforce_budget=True the expensive backend scores -1
    router = Router(RouterConfig(strategy="balanced", enforce_budget=True))
    req = make_req(input_tokens=1000, complexity=0.8, max_cost_usd=0.001)
    decision = router.route(req, seed=10)
    assert decision.chosen_backend == "fast-cheap"
