"""Tests for xai_diff.py"""

import numpy as np
import pytest
from xai_diff import (
    load_and_split,
    train_model,
    compute_disagreement,
    shap_importances,
    local_linear_importances,
)


def test_load_and_split_shapes():
    X_train, X_test, y_train, y_test, feature_names = load_and_split()
    # Breast cancer: 569 samples, 30 features
    assert X_train.shape[1] == 30
    assert len(feature_names) == 30
    assert X_train.shape[0] + X_test.shape[0] == 569


def test_model_accuracy():
    X_train, X_test, y_train, y_test, _ = load_and_split()
    model = train_model(X_train, y_train)
    acc = model.score(X_test, y_test)
    assert acc > 0.90, f"Expected accuracy > 0.90, got {acc:.3f}"


def test_compute_disagreement_perfect_agreement():
    """When both methods return identical values, rho should be 1.0."""
    vals = np.array([[0.5, -0.3, 0.1, 0.8, -0.2]])
    df = compute_disagreement(vals, vals.copy(), ["a", "b", "c", "d", "e"])
    assert df.iloc[0]["spearman_rho"] == pytest.approx(1.0)
    assert df.iloc[0]["sign_agreement"] == pytest.approx(1.0)


def test_compute_disagreement_reversed_ranking():
    """Completely reversed absolute-importance order gives rho = -1.0."""
    shap_v = np.array([[1.0, 0.8, 0.6, 0.4, 0.2]])
    local_v = np.array([[0.2, 0.4, 0.6, 0.8, 1.0]])
    df = compute_disagreement(shap_v, local_v, ["a", "b", "c", "d", "e"])
    assert df.iloc[0]["spearman_rho"] == pytest.approx(-1.0)


def test_compute_disagreement_output_schema():
    rng = np.random.default_rng(0)
    vals_a = rng.standard_normal((4, 6))
    vals_b = rng.standard_normal((4, 6))
    names = [f"f{i}" for i in range(6)]
    df = compute_disagreement(vals_a, vals_b, names)
    required = {
        "instance",
        "spearman_rho",
        "sign_agreement",
        "max_rank_diff",
        "top_disagree_feature",
        "shap_rank",
        "local_rank",
    }
    assert required.issubset(set(df.columns))
    assert len(df) == 4
    assert set(df["top_disagree_feature"]).issubset(set(names))


def test_shap_and_local_shapes():
    import pandas as pd
    from sklearn.datasets import load_breast_cancer
    from sklearn.model_selection import train_test_split

    data = load_breast_cancer()
    Xt, Xs, yt, _ = train_test_split(data.data, data.target, test_size=0.1, random_state=0)
    model = train_model(pd.DataFrame(Xt), yt)

    sv = shap_importances(model, pd.DataFrame(Xs[:5]), pd.DataFrame(Xt[:50]))
    lv = local_linear_importances(model.predict_proba, Xs[:5], Xt, n_perturb=100)
    assert sv.shape == (5, 30)
    assert lv.shape == (5, 30)
