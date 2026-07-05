# xai-explanation-diff

Diff SHAP vs a local-linear surrogate (the core of LIME) on a shared tabular
classifier. Surfaces instances and features where the two XAI methods disagree
most on feature importance.

## What it does

1. Trains a `GradientBoostingClassifier` on the sklearn breast-cancer dataset
   (569 samples, 30 features, binary label).
2. For each test instance computes:
   - **SHAP** values via `TreeExplainer` (game-theoretic, exact for tree ensembles).
   - **Local-linear surrogate** weights via weighted Ridge regression on 500
     Gaussian perturbations (same algorithmic core as LIME, implemented inline
     to avoid a broken package dependency).
3. Measures disagreement per instance:
   - Spearman rank correlation on absolute importances (1 = perfect agreement).
   - Sign agreement (fraction of features where both methods agree on direction).
   - Worst-case rank gap (which single feature is displaced most in the ranking).
4. Prints a report surfacing the most-disagreed instances and the features that
   sit at the centre of rank disagreements most often.

## How to run

```bash
pip install scikit-learn shap scipy numpy pandas
python xai_diff.py             # default: 50 test instances
python xai_diff.py --n 100     # more instances, slower
python -m pytest test_xai_diff.py -v
```

## Findings (50-instance run)

| metric | value |
|---|---|
| Model test accuracy | 0.956 |
| Mean instance-level Spearman rho | 0.583 |
| Mean sign agreement | 0.426 |
| Global rho (averaged importances) | 0.837 |

**Global vs local gap.** Global rank correlation (0.837) is substantially
higher than the mean instance-level correlation (0.583). The two methods broadly
agree on which features matter overall but diverge considerably for individual
instances - particularly boundary cases where the model prediction is uncertain.

**Sign disagreement is common.** Sign agreement of 0.426 means that for a
typical instance the two methods disagree on the direction of more than half the
features. This is partly a scale artefact: SHAP values are in probability space
while local-linear coefficients are in normalised perturbation space, so small
absolute values can flip sign with noise.

**Recurring disagreement features.** `mean compactness` (10/50 instances) and
`mean area` (5/50) sit at the centre of worst rank gaps most often. These are
features that SHAP assigns modest global importance but whose local linear
approximation is sensitive to the neighbourhood geometry.

**Magnitude difference.** SHAP magnitudes are roughly 18x larger than
local-linear magnitudes for top features (e.g., `worst concave points`: 1.32 vs
0.07 mean absolute value). Normalise before comparing directions.

## Scope

- Single dataset (breast cancer), single model family (gradient boosting).
- Local-linear surrogate uses Gaussian perturbations without LIME's original
  discretisation step; results are directionally similar but not identical to
  the published LIME algorithm.
- No visualisation; output is console text and a returned DataFrame.

## Out of scope

- Continuous re-training or active-learning loops.
- Neural network models (SHAP DeepExplainer / GradientExplainer).
- Multiple datasets or model families.
- Formal statistical significance testing of disagreement rates.
