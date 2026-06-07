# Model Card - Loan Risk Scorer v1.0

## Model Details

- **Type:** Gradient-boosted classifier
- **Framework:** scikit-learn 1.4
- **Owner:** Risk Analytics team

## Intended Use

Assist loan officers in triaging applications. Output is advisory only.

## Limitations

- Does not account for macroeconomic shocks.
- Performance degrades on applicants outside the training distribution.

## Fairness

Disparate impact analysis performed across gender and age cohorts.
See `evaluate.py` for audit results.

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Feedback loop bias | Medium | Quarterly retraining review |
| Regulatory non-compliance | High | Legal sign-off required before deployment |
