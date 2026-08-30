# synthetic-audit-trail

Generates synthetic but realistic AI-system audit trail events in JSONL or CSV
format. Designed to give compliance-tool developers a data source they can test
against without relying on real user traffic.

## What it does

`generate.py` produces a stream of audit events drawn from five realistic event
types:

| Event type | Approx. share | Extra fields |
|---|---|---|
| `inference_request` | 50% | `input_tokens`, `output_tokens`, `risk_tier`, `policy_result` |
| `tool_invocation` | 25% | `tool_name`, `input_tokens` |
| `policy_check` | 15% | `policy_result`, `risk_tier` |
| `content_filter` | 7% | `policy_result` |
| `error` | 3% | `error_code` |

All events carry: `event_id`, `event_type`, `timestamp`, `session_id`,
`user_id`, `model_id`, `latency_ms`, and `anomaly` (bool).

Latency values follow a log-normal distribution around realistic means. A
configurable fraction of events are flagged as anomalies and receive a latency
spike (5x-20x the baseline) so that anomaly-detection logic in compliance tools
can be exercised.

## How to run

```bash
# install test dependency
pip install -r requirements.txt

# 100 events to stdout (JSONL, default)
python generate.py

# 1000 events to a file, fixed seed, CSV format
python generate.py -n 1000 --seed 42 --format csv -o trail.csv

# 500 events with 5% anomalies
python generate.py -n 500 --anomaly-rate 0.05

# run tests
python -m pytest test_generate.py -v
```

## CLI options

| Flag | Default | Description |
|---|---|---|
| `-n` / `--count` | 100 | Number of events |
| `-o` / `--output` | `-` (stdout) | Output file path |
| `--seed` | None | Fix random seed for reproducibility |
| `--anomaly-rate` | 0.02 | Fraction of events marked as anomalies |
| `--format` | `jsonl` | `jsonl` or `csv` |

## Findings

- A pool of 50 synthetic users and 200 sessions produces realistic
  co-occurrence patterns without explicit session-modelling.
- Log-normal latency captures the long-tail character of real inference calls
  better than a uniform or normal distribution.
- Pinning the seed makes the generator deterministic, which is essential for
  regression-testing compliance tools against a known corpus.

## Scope

In scope:
- Single-day event windows with randomised per-minute offsets.
- Five event types covering the most common audit categories for LLM systems.
- JSONL and CSV output.
- Anomaly injection via latency spikes and the `anomaly` flag.

Out of scope:
- Sequential causality between events (e.g. a tool call following an
  inference request in the same session).
- Multi-day rolling windows or time-zone-aware business-hours distributions.
- PII or secret injection for redaction testing (see the `prompt-redactor`
  experiment for that).
