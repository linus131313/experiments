import pytest
from redactor import redact, redact_to_json


def test_email_redacted():
    r = redact("Contact alice@example.com for help.")
    assert "[EMAIL]" in r.redacted
    assert "alice@example.com" not in r.redacted
    assert any(f.label == "email" for f in r.findings)


def test_ssn_and_credit_card():
    text = "SSN: 123-45-6789  card: 4111 1111 1111 1111"
    r = redact(text)
    assert "[SSN]" in r.redacted
    assert "[CREDIT_CARD]" in r.redacted
    assert "123-45-6789" not in r.redacted
    assert "4111 1111 1111 1111" not in r.redacted


def test_aws_key_redacted():
    r = redact("export AWS_KEY=AKIAIOSFODNN7EXAMPLE")
    assert "[AWS_KEY]" in r.redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in r.redacted
    assert r.findings[0].category == "secret"


def test_jwt_redacted():
    jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        ".dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    )
    r = redact(f"Bearer {jwt}")
    assert "[JWT_TOKEN]" in r.redacted
    assert jwt not in r.redacted


def test_clean_text_untouched():
    text = "Hello world, nothing sensitive here."
    r = redact(text)
    assert r.redacted == text
    assert r.findings == []


def test_redact_to_json_valid():
    import json
    out = redact_to_json("email is test@foo.com and token: AKIAIOSFODNN7EXAMPLE")
    data = json.loads(out)
    assert "redacted" in data
    assert data["summary"]["total"] >= 2
