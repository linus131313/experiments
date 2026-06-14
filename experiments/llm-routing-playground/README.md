# llm-routing-playground

Toy cost/latency-aware router that dispatches requests between two mock LLM backends and visualises the routing decisions.

## What it does

Two mock backends simulate realistic cost and quality profiles:

| Backend | Cost (input/output per 1k tokens) | Base latency | Quality (simple/complex) |
|---|---|---|---|
| fast-cheap | $0.0005 / $0.0015 | 120ms | 0.92 / 0.61 |
| slow-expensive | $0.015 / $0.075 | 1800ms | 0.97 / 0.91 |

The router supports four strategies:

- **cost** - always pick the cheaper backend
- **latency** - always pick the faster backend
- **quality** - always pick the higher-quality backend
- **balanced** - weighted score combining quality, normalised cost, and normalised latency; hard budget and latency caps are applied first

The visualiser prints a routing-decision table and a complexity-bucket bar chart for each strategy run.

## How to run

No external dependencies beyond the standard library.

```bash
cd experiments/llm-routing-playground

# Run all four strategies
python main.py

# Run a single strategy
python main.py balanced
python main.py cost
```

Run the tests:

```bash
pip install pytest
python -m pytest test_router.py -v
```

## Findings

With realistic cost ratios (~30-60x difference between the two backends), the balanced scorer with default weights (quality=0.5, cost=0.3, latency=0.2) still routes every request to the cheap backend. The cost normalisation divides each backend's cost by the maximum for that request, so the slow backend always scores near -0.5 on the combined cost+latency term, which wipes out its quality advantage (at most +0.3 in the quality term).

The quality-only strategy pays 60x more for an average of 18 percentage-points of quality improvement (0.76 -> 0.94) - a steep curve that is only worth it for tasks where correctness is critical and cost is unconstrained.

Key takeaway: a balanced router needs explicit complexity-aware thresholds (e.g. "route to expensive backend only if complexity > 0.7 AND latency budget > 5s") rather than a single weight vector, because the weight vector gets dominated by whichever dimension has the largest absolute spread.

## Scope

- All backends are mocks with no real network calls.
- Quality scores are simulated; they are not calibrated against real model benchmarks.
- No streaming, token counting, or retry logic.

## Out of scope

- Real API integration (OpenAI, Anthropic, etc.)
- Online learning / adaptive threshold tuning
- Multi-tenant request queuing
