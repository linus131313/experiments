# agent-reliability-eval

Tiny eval framework for five agent reliability patterns, run on a mock
tool so no external dependencies or API keys are needed.

## Patterns

| Pattern | Description |
|---|---|
| `naive` | Single attempt; accept any non-error result |
| `retry(3)` | Retry on failure up to 3 times with exponential backoff |
| `fallback` | Try primary; switch to secondary on failure |
| `retry(2)+fallback` | Retry primary twice, then try secondary once |
| `grounded` | Validate output schema before accepting a result |

## Mock tool setup

Two mock tools are configured to drive the eval:

- **primary** - 60% success rate, 10% format-error rate (API says OK but
  body is malformed), 100 ms simulated latency
- **secondary** - 85% success rate, 2% format-error rate, 250 ms latency

Each pattern gets a freshly seeded copy of the tools to ensure
reproducible comparisons.

## How to run

```
python eval.py
```

```
python -m pytest test_eval.py -v
```

No packages beyond pytest are required.

## Results (500 trials per query, 5 queries)

```
Pattern                 Success%  Avg calls   Avg ms
-------------------------------------------------------
naive                      60.2%       1.00    100.0
retry(3)                   94.3%       1.56    191.2
fallback                   94.6%       1.40    199.6
retry(2)+fallback          97.8%       1.56    199.1
grounded                   54.3%       1.00    100.0
```

## Findings

- **Retry vs fallback at similar success rates**: `retry(3)` and `fallback`
  both reach ~94% success but through different trade-offs. Retry averages
  more calls against the same primary tool; fallback uses a second tool with
  a shorter queue of attempts. When the secondary tool is cheaper or faster,
  fallback is preferable.

- **Combining them pays off**: `retry(2)+fallback` reaches ~98% success at
  only ~1.56 avg calls - the same call budget as `retry(3)` but ~3.5 pp
  higher success, because the secondary tool is more reliable.

- **Grounded reveals a hidden quality gap**: naive reports 60% success,
  but 6 pp of those results are format errors that downstream code would
  reject. The grounded pattern filters them, dropping apparent success to
  54% but returning only well-formed answers. The right choice depends on
  whether the consumer validates inputs itself.

- **Latency grows with safety**: going from naive (100 ms) to
  `retry(2)+fallback` (~199 ms) roughly doubles average latency. The
  ceiling is largely determined by the secondary tool's latency rather than
  the retry backoff.

## Scope

- Mock tools only - no real HTTP calls or model inference.
- Single-step tool use (one query, one result). Multi-step chains are
  out of scope.
- Patterns are evaluated independently; combining e.g. grounded with retry
  is left as an extension.
