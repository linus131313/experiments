# eu-ai-act-tier-classifier

A lightweight, rule-based classifier that maps an AI use-case description to one
of the four EU AI Act risk tiers, with citations to the relevant articles.

## What it does

Given a plain-text description of an AI system, the classifier returns:

- **Risk tier** - Unacceptable / High / Limited / Minimal
- **Confidence** - high / medium / low (based on how many keyword rules matched)
- **Matched rules** - which specific criteria triggered the classification
- **Citations** - relevant EU AI Act articles (Art. 5, Art. 6, Annex III, Art. 50)
- **Summary** - a human-readable explanation

Rules are hand-coded from the official EU AI Act text (Regulation (EU) 2024/1689)
and cover all four tiers in priority order (Unacceptable beats High, etc.).

## How to run

No dependencies beyond Python 3.10+.

```bash
# Pass a description as an argument
python classifier.py "A system that screens job applicants using AI."

# Read from stdin
echo "A customer support chatbot" | python classifier.py -
```

### Example output

```
Risk Tier:  High  (confidence: medium)
Summary:    This use case is likely High Risk under the EU AI Act (Art. 6 and
            Annex III). Conformity assessment, registration, and ongoing
            monitoring are required. Matched: AI in employment and workers
            management.
Citations:  Art. 6(2), Annex III(4)
Matched rules:
  - AI in employment and workers management
```

## Run tests

```bash
python -m pytest test_classifier.py -v
```

## Findings

- Keyword matching catches the majority of clear-cut cases with medium-to-high confidence.
- Context keywords are necessary to avoid false positives: emotion detection only
  escalates to Unacceptable when the description also mentions a workplace or
  educational setting.
- Higher tiers always win: a description matching both Limited and High rules
  is classified High.
- Confidence correlates with the number of rule hits, giving a rough measure of
  how on-the-nose the description is.

## Scope

- Rule-based only; no ML model involved.
- Covers the four risk tiers as defined in Regulation (EU) 2024/1689 (final text).
- Checks the Annex III list of High Risk use cases exhaustively.
- Does not handle the Art. 6(1) pathway for AI used as safety components in
  Annex I regulated products (medical devices, machinery, etc.).

## Out of scope

- GPAI (General Purpose AI) model obligations (Art. 51-55).
- Operator vs. deployer obligation split.
- Sectoral guidance from national supervisory authorities.
- Any jurisdiction outside the EU.
- Nuanced edge cases that require legal interpretation of the Act.
