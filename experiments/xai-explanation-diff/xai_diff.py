"""
xai_diff.py - Compare SHAP and local-linear-surrogate (LIME-style) explanations
on a shared tabular classifier. Surfaces instances and features where the two
methods disagree most on feature importance.

Usage:
    python xai_diff.py           # run on 50 test instances
    python xai_diff.py --n 100   # run on 100 test instances
"""

import argparse
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
import shap


# ---------------------------------------------------------------------------
# Data and model
# ---------------------------------------------------------------------------

def load_and_split(random_state: int = 42):
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = data.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    return X_train, X_test, y_train, y_test, list(data.feature_names)


def train_model(X_train, y_train, random_state: int = 42):
    model = GradientBoostingClassifier(
        n_estimators=100, random_state=random_state
    )
    model.fit(X_train, y_train)
    return model


# ---------------------------------------------------------------------------
# SHAP explanations
# ---------------------------------------------------------------------------

def shap_importances(model, X_sample, X_background) -> np.ndarray:
    """
    Return a (n_samples, n_features) array of SHAP values for class 1.
    Uses TreeExplainer with a background dataset for better baseline estimates.
    """
    explainer = shap.TreeExplainer(model, X_background)
    values = explainer.shap_values(X_sample)
    # Older shap versions return a list [class0, class1]; newer return 2-D directly
    if isinstance(values, list):
        values = values[1]
    return np.array(values)


# ---------------------------------------------------------------------------
# Local linear surrogate (LIME-style)
# ---------------------------------------------------------------------------

def local_linear_importances(
    predict_fn,
    X_sample: np.ndarray,
    X_train: np.ndarray,
    n_perturb: int = 500,
    kernel_width_factor: float = 0.75,
    random_state: int = 42,
) -> np.ndarray:
    """
    Compute local linear surrogate feature weights (LIME-style) for each row
    in X_sample. Returns a (n_samples, n_features) array.

    Algorithm per instance:
      1. Sample perturbations from N(0, 1) in feature space.
      2. Translate to original scale using per-feature std from X_train.
      3. Weight by Gaussian kernel of Euclidean distance in normalised space.
      4. Fit a weighted Ridge regression; coefficients are the importances.
    """
    rng = np.random.RandomState(random_state)
    n_features = X_sample.shape[1]
    feature_std = X_train.std(axis=0)
    # Avoid zero-std features causing NaN
    feature_std = np.where(feature_std == 0, 1.0, feature_std)

    kernel_width = np.sqrt(n_features) * kernel_width_factor
    all_weights = np.zeros((len(X_sample), n_features))

    for i in range(len(X_sample)):
        instance = X_sample[i]

        # Normalised perturbations
        z = rng.normal(0, 1, size=(n_perturb, n_features))
        # Actual perturbed data points in original scale
        x_perturb = instance + z * feature_std

        # Kernel weights based on distance in normalised space
        distances = np.sqrt((z ** 2).sum(axis=1))
        kw = np.exp(-(distances ** 2) / (2 * kernel_width ** 2))

        # Target: model probability for class 1
        probs = predict_fn(x_perturb)[:, 1]

        # Weighted Ridge regression on normalised perturbations
        reg = Ridge(alpha=1.0)
        reg.fit(z, probs, sample_weight=kw)
        all_weights[i] = reg.coef_

    return all_weights


# ---------------------------------------------------------------------------
# Disagreement metrics
# ---------------------------------------------------------------------------

def compute_disagreement(
    shap_vals: np.ndarray,
    local_vals: np.ndarray,
    feature_names: list,
) -> pd.DataFrame:
    """
    For each instance compute:
      - spearman_rho: rank correlation between absolute importances (1 = agree).
      - sign_agreement: fraction of features where both methods give same sign.
      - max_rank_diff: largest rank-position gap for any single feature.
      - top_disagree_feature: feature name at the centre of worst rank gap.
    """
    n_samples = shap_vals.shape[0]
    records = []

    for i in range(n_samples):
        sv = shap_vals[i]
        lv = local_vals[i]

        rho, _ = spearmanr(np.abs(sv), np.abs(lv))

        both_nz = (sv != 0) & (lv != 0)
        if both_nz.sum() > 0:
            sign_agree = float(
                np.mean(np.sign(sv[both_nz]) == np.sign(lv[both_nz]))
            )
        else:
            sign_agree = float("nan")

        shap_ranks = np.argsort(np.argsort(-np.abs(sv)))
        lime_ranks = np.argsort(np.argsort(-np.abs(lv)))
        rank_diffs = np.abs(shap_ranks - lime_ranks)
        worst_feat = int(np.argmax(rank_diffs))

        records.append(
            {
                "instance": i,
                "spearman_rho": round(float(rho), 4) if not np.isnan(rho) else np.nan,
                "sign_agreement": round(sign_agree, 4),
                "max_rank_diff": int(rank_diffs[worst_feat]),
                "top_disagree_feature": feature_names[worst_feat],
                "shap_rank": int(shap_ranks[worst_feat]),
                "local_rank": int(lime_ranks[worst_feat]),
            }
        )

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def summarize(
    df: pd.DataFrame,
    shap_vals: np.ndarray,
    local_vals: np.ndarray,
    feature_names: list,
    top_k: int = 5,
):
    print(f"Instances analysed : {len(df)}")
    print(f"Features           : {len(feature_names)}")
    print(
        f"Mean Spearman rho  : {df['spearman_rho'].mean():.3f}  "
        f"(1=perfect agreement, -1=perfect disagreement)"
    )
    print(f"Mean sign agreement: {df['sign_agreement'].mean():.3f}")
    print()

    print(f"Top {top_k} instances with lowest rank correlation (most disagreement):")
    cols = ["instance", "spearman_rho", "sign_agreement", "top_disagree_feature"]
    worst = df.nsmallest(top_k, "spearman_rho")[cols]
    print(worst.to_string(index=False))
    print()

    print(f"Features most often at centre of worst rank gap:")
    counts = df["top_disagree_feature"].value_counts().head(top_k)
    print(counts.to_string())
    print()

    # Global feature-level stats
    shap_mean_abs = np.abs(shap_vals).mean(axis=0)
    local_mean_abs = np.abs(local_vals).mean(axis=0)
    global_rho, _ = spearmanr(shap_mean_abs, local_mean_abs)
    print(f"Global rank correlation (mean |importance| across instances): {global_rho:.3f}")

    feat_df = pd.DataFrame(
        {
            "feature": feature_names,
            "shap_mean_abs": shap_mean_abs,
            "local_mean_abs": local_mean_abs,
        }
    ).sort_values("shap_mean_abs", ascending=False)
    print("\nTop 10 features by mean |SHAP|:")
    print(feat_df.head(10).to_string(index=False))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(n_sample: int = 50, random_state: int = 42) -> pd.DataFrame:
    print("Loading breast-cancer dataset and splitting...")
    X_train, X_test, y_train, y_test, feature_names = load_and_split(random_state)
    print(f"  train={len(X_train)}, test={len(X_test)}, features={len(feature_names)}")

    print("Training GradientBoostingClassifier...")
    model = train_model(X_train, y_train, random_state)
    accuracy = model.score(X_test, y_test)
    print(f"  Test accuracy: {accuracy:.3f}")

    n_sample = min(n_sample, len(X_test))
    X_sample = X_test.iloc[:n_sample]

    print(f"\nComputing SHAP values for {n_sample} instances...")
    sv = shap_importances(model, X_sample, X_train)

    print(f"Computing local-linear-surrogate values for {n_sample} instances...")
    lv = local_linear_importances(
        model.predict_proba,
        X_sample.values,
        X_train.values,
        n_perturb=500,
        random_state=random_state,
    )

    print("\nComputing disagreement metrics...")
    df = compute_disagreement(sv, lv, feature_names)

    print("\n=== XAI Explanation Diff Report ===\n")
    summarize(df, sv, lv, feature_names)

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diff SHAP vs local-linear explanations")
    parser.add_argument("--n", type=int, default=50, help="number of test instances to explain")
    args = parser.parse_args()
    run(n_sample=args.n)
