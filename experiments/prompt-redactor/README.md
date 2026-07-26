# prompt-redactor

Regex + entropy-based classifier pipeline that strips obvious PII and secrets
from text before it reaches a language model.

## What it does

Two-stage pipeline:

1. **Regex stage** - 12 patterns covering common PII (email, SSN, credit card,
   US phone, IPv4) and secrets (JWT, AWS access key, GitHub tokens, private key
   headers, generic API key / password assignments, long hex blobs).

2. **Classifier stage** - Shannon entropy of each matched span adjusts the
   pattern's base confidence up or down. High-entropy strings (random-looking
   keys) gain confidence; low-entropy strings (e.g. "123456") lose it. Spans
   below `min_confidence` (default 0.60) are kept untouched.

Matched spans are replaced with labeled placeholders such as `[EMAIL]`,
`[AWS_KEY]`, `[JWT_TOKEN]`, `[SSN]`, etc.

## How to run

```
pip install -r requirements.txt
```

Pipe text in via stdin:

```
echo "My SSN is 123-45-6789 and key is AKIAIOSFODNN7EXAMPLE" | python redactor.py
```

Or pass a file path:

```
python redactor.py prompt.txt
```

Output is JSON:

```json
{
  "redacted": "My SSN is [SSN] and key is [AWS_KEY]",
  "summary": { "total": 2, "by_category": { "pii": 1, "secret": 1 } },
  "findings": [
    { "category": "pii", "label": "ssn", "confidence": 0.92, "original_length": 11 },
    { "category": "secret", "label": "aws_key", "confidence": 0.99, "original_length": 20 }
  ]
}
```

Use the Python API directly:

```python
from redactor import redact

result = redact("Contact me at foo@bar.com")
print(result.redacted)   # "Contact me at [EMAIL]"
print(result.findings)   # [Finding(category='pii', label='email', ...)]
```

## Running tests

```
python -m pytest test_redactor.py -v
```

## Findings

- Pure-regex recall is high for well-formatted tokens (AWS keys, JWTs, SSNs
  with dashes). Recall drops for free-form data like names or addresses that
  have no canonical structure.
- Entropy adjustment helps cut false positives from the `hex_secret` pattern,
  which would otherwise match short version hashes like `deadbeef`.
- The `generic_api_key` pattern (context-keyed) catches most `key=VALUE` style
  assignments across many naming conventions without needing a hardcoded list
  of provider prefixes.
- IPv4 matching is intentionally conservative (requires valid octet ranges) to
  avoid triggering on version strings like `1.2.3.4` in dependency lines.

## Scope

Covers:
- Email addresses
- US Social Security Numbers (ddd-dd-dddd format)
- US phone numbers (with and without country code)
- Credit card numbers (16-digit, common separators)
- IPv4 addresses (valid octet range only)
- AWS IAM access key IDs (AKIA prefix)
- GitHub personal / OAuth / server tokens
- JWT tokens (header.payload.signature format)
- PEM private key headers
- Generic `api_key = VALUE` and `password = VALUE` assignments
- Long hex strings (>=40 chars) with high entropy

Out of scope:
- Names and addresses (no structural pattern)
- Non-US phone formats
- IBAN / routing numbers
- API keys without context keywords and non-hex random strings under 40 chars
- ML-based NER (would add heavy dependencies)
