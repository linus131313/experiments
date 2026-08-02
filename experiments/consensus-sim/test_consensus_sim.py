"""Tests for consensus_sim."""
import pytest
from consensus_sim import ConsensusSim, run_sweep


def test_no_byzantine_always_agrees():
    """With zero Byzantine agents every honest agent decides the same value."""
    for seed in range(30):
        r = ConsensusSim(5, 0, seed=seed).run()
        assert r["agreed"], f"Expected agreement with f=0, seed={seed}"


def test_single_agent_agrees():
    """A single honest agent trivially agrees with itself."""
    r = ConsensusSim(1, 0, seed=0).run()
    assert r["agreed"]
    assert r["consensus_value"] in (0, 1)


def test_determinism():
    """Same constructor seed produces identical results."""
    r1 = ConsensusSim(7, 2, seed=99).run()
    r2 = ConsensusSim(7, 2, seed=99).run()
    assert r1 == r2


def test_bft_flag_correct():
    """bft_threshold_met reflects n > 3f correctly."""
    assert ConsensusSim(7, 2, seed=0).run()["bft_threshold_met"] is True
    assert ConsensusSim(6, 2, seed=0).run()["bft_threshold_met"] is False
    assert ConsensusSim(4, 1, seed=0).run()["bft_threshold_met"] is True


def test_invalid_params_raise():
    """Bad (n, f) values raise ValueError."""
    with pytest.raises(ValueError):
        ConsensusSim(0, 0)
    with pytest.raises(ValueError):
        ConsensusSim(4, -1)
    with pytest.raises(ValueError):
        ConsensusSim(4, 4)


def test_all_adversary_strategies_run():
    """All adversary strategies return a valid result dict."""
    for strategy in ("adaptive", "random", "collude1"):
        r = ConsensusSim(7, 2, seed=42).run(adversary=strategy)
        assert "agreed" in r
        assert "bft_threshold_met" in r
        assert r["n"] == 7
        assert r["f"] == 2


def test_sweep_produces_rows():
    """run_sweep returns one row per (n, f) pair."""
    rows = run_sweep(max_n=4, trials=5)
    # n in 1..4, f in 0..n-1: 1 + 2 + 3 + 4 = 10 rows
    assert len(rows) == 10
    for row in rows:
        assert 0.0 <= row["agreement_rate"] <= 1.0
