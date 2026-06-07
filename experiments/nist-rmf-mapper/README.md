# nist-rmf-mapper

Maps concrete code artifacts in a project directory to NIST AI Risk Management
Framework (AI RMF 1.0) functions and categories, producing a Markdown compliance
coverage report.

## What it does

1. Scans a project directory and classifies files into artifact types:
   - `tests` - test files (test_*.py, in tests/ subdirectory, etc.)
   - `model_card` - model card documents (model_card.md, modelcard.*)
   - `audit` - audit trail files (audit_log.json, audit_*.*)
   - `docs` - README, CONTRIBUTING, CHANGELOG, files in docs/
   - `policy` - governance and policy files (policy.yaml, governance_*.*)
   - `eval` - evaluation and benchmark scripts (evaluate.py, metrics.py, etc.)
   - `logs` - Python files that use the `logging` module
2. Matches each artifact type to the NIST AI RMF categories that the artifact
   provides evidence for (GOVERN, MAP, MEASURE, MANAGE).
3. Renders a Markdown report: a summary table showing which categories are covered
   and which are gaps, followed by per-category artifact lists.

This is useful for a quick compliance scoping exercise - paste the report into a
risk register to see where you have evidence and where you need to add controls.

## How to run

```bash
pip install -r requirements.txt

# Print report to stdout
python mapper.py demo/

# Write report to file
python mapper.py demo/ -o report.md
```

Run tests:

```bash
pytest test_mapper.py -v
```

## Demo

The `demo/` directory models a toy loan-risk-scoring project with one file per
artifact type. Running the mapper against it covers all 19 categories across the
four NIST functions.

```
demo/
  README.md                      -> docs
  model_card.md                  -> model_card
  audit_log.json                 -> audit
  evaluate.py                    -> eval (also uses logging)
  tests/test_model.py            -> tests
  config/governance_policy.yaml  -> policy
```

## Findings

- The artifact-type heuristics are coarse but sufficient for a first-pass gap
  analysis. A project with tests, a model card, an audit log, and a policy file
  covers all four NIST functions.
- GOVERN categories rely heavily on `docs` and `policy` - projects that keep
  governance information only in internal wikis will show false gaps.
- MEASURE-3 (risk tracking over time) requires either structured logs or audit
  entries; a bare test suite is not enough.

## Out of scope

- Semantic analysis of artifact content (e.g., checking that a model card is
  complete vs. just named model_card.md).
- Subcategory-level mapping (AI RMF has ~70 subcategories; this maps to the
  19 top-level categories only).
- Integration with ticketing or GRC systems.
- Continuous monitoring - the tool is a point-in-time scanner.
