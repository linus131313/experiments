# agent-failure-taxonomy

Structured YAML taxonomy of observed agent failure modes in LLM-based systems,
paired with a small visualiser that renders the taxonomy as an ASCII tree,
severity breakdown, or Mermaid mindmap.

## What it does

`taxonomy.yaml` catalogues 19 failure modes across 6 categories:

| Category | Failures |
|---|---|
| Goal Interpretation | goal-drift, ambiguity-collapse, scope-creep |
| Planning | missing-precondition, circular-plan, over-decomposition |
| Tool Use | hallucinated-tool-call, argument-type-error, ignored-tool-output, tool-result-fabrication |
| Context Management | context-overflow-truncation, stale-state-reference, contradictory-belief |
| Execution | retry-storm, partial-completion, unintended-side-effect |
| Self-Assessment | overconfidence, failure-denial, poor-termination |

Each entry includes:
- **severity** - critical / high / medium / low
- **description** - what goes wrong
- **signals** - observable indicators to detect the failure
- **mitigations** - concrete countermeasures
- **examples** - brief concrete scenario

`visualise.py` renders the taxonomy in three modes:

- Default: ASCII tree + severity/category breakdown
- `--stats`: severity/category counts only
- `--mermaid`: Mermaid mindmap markup (paste into any Mermaid renderer)

## How to run

```bash
pip install -r requirements.txt

# ASCII tree + stats
python visualise.py

# severity/category counts only
python visualise.py --stats

# Mermaid mindmap
python visualise.py --mermaid

# Run tests
pytest test_taxonomy.py -v
```

## Findings

- Tool use failures dominate the critical/high tier. Hallucinated tool calls and
  fabricated results are the hardest to detect because they do not produce
  runtime exceptions.
- Self-assessment failures (overconfidence, failure denial) tend to suppress
  other failure signals, making them multipliers - they hide the presence of
  other failure modes.
- Most mitigations fall into one of three patterns: boundary validation (check
  inputs/outputs at tool edges), budgeting (cap retries, steps, cost), and
  explicit state tracking (belief ledger, completion checklist).

## Scope

- Covers LLM-based agents using tool/function calling; not specific to any
  framework.
- Failure modes are based on patterns reported in the literature and
  common practitioner experience; not derived from a systematic empirical study.
- The severity ratings are qualitative assessments, not statistically calibrated.

## Out of scope

- Failures specific to multi-agent coordination (covered in consensus-sim).
- RAG retrieval failures (covered in rag-robustness-eval).
- Prompt injection and adversarial inputs (covered in mcp-prompt-injection-corpus).
