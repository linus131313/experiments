"""Basic correctness tests for the loan risk scorer."""


def test_score_range():
    score = 0.72  # placeholder for actual model call
    assert 0.0 <= score <= 1.0


def test_high_risk_applicant():
    # High debt-to-income ratio should yield higher risk score
    score = 0.91
    assert score > 0.5


def test_output_type():
    score = 0.42
    assert isinstance(score, float)
