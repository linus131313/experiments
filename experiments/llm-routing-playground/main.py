"""Demo: run a batch of requests through the router and visualize decisions."""

import sys
from router import Router, RouterConfig, Request
from visualizer import print_decision_table, print_summary

STRATEGIES = ["cost", "latency", "quality", "balanced"]

DEMO_REQUESTS = [
    # tight budget/latency - fast wins
    Request(input_tokens=200,  complexity=0.1,  latency_budget_ms=500,   max_cost_usd=0.001, label="classify-short"),
    Request(input_tokens=400,  complexity=0.2,  latency_budget_ms=1000,  max_cost_usd=0.005, label="summarize-short"),
    # relaxed budget - quality or balanced can pick slow
    Request(input_tokens=800,  complexity=0.5,  latency_budget_ms=5000,  max_cost_usd=0.50, label="extract-medium"),
    Request(input_tokens=1200, complexity=0.7,  latency_budget_ms=8000,  max_cost_usd=0.50, label="reason-medium"),
    Request(input_tokens=2000, complexity=0.9,  latency_budget_ms=10000, max_cost_usd=1.00, label="code-complex"),
    Request(input_tokens=300,  complexity=0.15, latency_budget_ms=400,   max_cost_usd=0.002, label="qa-simple"),
    Request(input_tokens=600,  complexity=0.6,  latency_budget_ms=6000,  max_cost_usd=0.50, label="translate"),
    Request(input_tokens=1500, complexity=0.85, latency_budget_ms=10000, max_cost_usd=1.00, label="essay-hard"),
]


def run_strategy(strategy: str) -> None:
    print(f"\n{'='*80}")
    print(f"  Strategy: {strategy.upper()}")
    print(f"{'='*80}")
    cfg = RouterConfig(strategy=strategy)
    router = Router(cfg)
    decisions = [router.route(req, seed=i + 1) for i, req in enumerate(DEMO_REQUESTS)]
    print_decision_table(decisions)
    print_summary(decisions)


if __name__ == "__main__":
    strategies = sys.argv[1:] if sys.argv[1:] else STRATEGIES
    for s in strategies:
        if s not in STRATEGIES:
            print(f"Unknown strategy '{s}'. Choose from: {STRATEGIES}")
            sys.exit(1)
        run_strategy(s)
