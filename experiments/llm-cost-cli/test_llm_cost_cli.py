import pytest
from llm_cost_cli import estimate, fuzzy_match, CostResult, MODELS


def test_exact_model_match():
    result = estimate("gpt-4o", 1000, 500)
    assert result.model == "gpt-4o"
    assert result.input_tokens == 1000
    assert result.output_tokens == 500


def test_cost_calculation():
    # gpt-4o: $2.50/1M input, $10.00/1M output
    result = estimate("gpt-4o", 1_000_000, 1_000_000)
    assert abs(result.input_cost - 2.50) < 1e-9
    assert abs(result.output_cost - 10.00) < 1e-9
    assert abs(result.total_cost - 12.50) < 1e-9


def test_fuzzy_match_substring():
    # "sonnet-5" should resolve to "claude-sonnet-5"
    resolved = fuzzy_match("claude-sonnet-5")
    assert resolved == "claude-sonnet-5"


def test_unknown_model_raises():
    with pytest.raises(ValueError, match="Unknown model"):
        estimate("definitely-not-a-real-model-xyz", 100, 100)


def test_zero_tokens_returns_zero_cost():
    result = estimate("gpt-4o-mini", 0, 0)
    assert result.total_cost == 0.0
    assert result.input_cost == 0.0
    assert result.output_cost == 0.0


def test_csv_format_contains_expected_fields():
    result = estimate("gpt-4o", 500, 250)
    csv_line = result.format("csv")
    parts = csv_line.split(",")
    assert len(parts) == 6
    assert parts[0] == "gpt-4o"
    assert int(parts[1]) == 500
    assert int(parts[2]) == 250
