"""
Prompt redactor: regex + entropy-based classifier pipeline
that strips PII and secrets from text before it reaches a model.

Pipeline:
  1. Regex patterns identify candidate spans.
  2. Shannon entropy classifier adjusts confidence per span.
  3. Threshold filter decides what gets replaced.
"""

import json
import math
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Finding:
    category: str   # "pii" or "secret"
    label: str      # e.g. "email", "aws_key"
    start: int
    end: int
    original: str
    confidence: float  # 0-1


@dataclass
class RedactionResult:
    original: str
    redacted: str
    findings: List[Finding]

    def summary(self) -> dict:
        by_cat: dict = {}
        for f in self.findings:
            by_cat[f.category] = by_cat.get(f.category, 0) + 1
        return {"total": len(self.findings), "by_category": by_cat}


# (category, label, pattern, base_confidence)
_PATTERNS = [
    # Secrets - high specificity
    ("secret", "jwt",
     r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
     0.98),
    ("secret", "aws_key",
     r"AKIA[0-9A-Z]{16}",
     0.99),
    ("secret", "gh_token",
     r"gh[pousr]_[A-Za-z0-9_]{36,}",
     0.99),
    ("secret", "private_key_header",
     r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
     0.99),
    # Secrets - context-keyed (group 2 = the value)
    ("secret", "generic_api_key",
     r"(?i)(?:api[_-]?key|apikey|token|secret)\s*[=:\"']\s*([A-Za-z0-9_\-]{20,})",
     0.82),
    ("secret", "password_in_text",
     r"(?i)(?:password|passwd|pwd)\s*[=:\"']\s*(\S{6,})",
     0.78),
    # Secrets - structural
    ("secret", "hex_secret",
     r"\b[0-9a-f]{40,64}\b",
     0.55),
    # PII
    ("pii", "email",
     r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
     0.95),
    ("pii", "ssn",
     r"\b\d{3}-\d{2}-\d{4}\b",
     0.92),
    ("pii", "credit_card",
     r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
     0.85),
    ("pii", "phone_us",
     r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b",
     0.78),
    ("pii", "ipv4",
     r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
     0.70),
]

_PLACEHOLDER = {
    ("secret", "jwt"):               "[JWT_TOKEN]",
    ("secret", "aws_key"):           "[AWS_KEY]",
    ("secret", "gh_token"):          "[GH_TOKEN]",
    ("secret", "private_key_header"): "[PRIVATE_KEY]",
    ("secret", "generic_api_key"):   "[API_KEY]",
    ("secret", "password_in_text"):  "[PASSWORD]",
    ("secret", "hex_secret"):        "[HEX_SECRET]",
    ("pii",    "email"):             "[EMAIL]",
    ("pii",    "ssn"):               "[SSN]",
    ("pii",    "credit_card"):       "[CREDIT_CARD]",
    ("pii",    "phone_us"):          "[PHONE]",
    ("pii",    "ipv4"):              "[IP_ADDRESS]",
}


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq: dict = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((cnt / n) * math.log2(cnt / n) for cnt in freq.values())


def _adjust_confidence(value: str, base: float) -> float:
    """Classifier step: shift base confidence by entropy of the matched value."""
    h = _shannon_entropy(value)
    if h >= 4.0:
        return min(1.0, base + 0.08)
    if h < 2.0:
        return max(0.0, base - 0.25)
    return base


def redact(text: str, min_confidence: float = 0.60) -> RedactionResult:
    """
    Scan text for PII and secrets, replace them with labeled placeholders.

    Parameters
    ----------
    text : str
        The input prompt or message.
    min_confidence : float
        Only redact findings at or above this threshold (0-1).

    Returns
    -------
    RedactionResult
        Contains the redacted string and a list of findings.
    """
    raw_findings: List[Finding] = []

    for category, label, pattern, base_conf in _PATTERNS:
        for m in re.finditer(pattern, text):
            # For patterns with a capture group, use it to score entropy
            key_part = m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)
            conf = _adjust_confidence(key_part, base_conf)
            if conf >= min_confidence:
                raw_findings.append(Finding(
                    category=category,
                    label=label,
                    start=m.start(),
                    end=m.end(),
                    original=m.group(0),
                    confidence=round(conf, 4),
                ))

    # Sort by start position, deduplicate overlapping spans (keep highest confidence)
    raw_findings.sort(key=lambda f: (f.start, -f.confidence))
    deduped: List[Finding] = []
    for f in raw_findings:
        if not any(f.start < d.end and f.end > d.start for d in deduped):
            deduped.append(f)

    # Replace from end of string backward to preserve offsets
    deduped_rev = sorted(deduped, key=lambda f: f.start, reverse=True)
    redacted = text
    for f in deduped_rev:
        placeholder = _PLACEHOLDER.get((f.category, f.label), f"[{f.label.upper()}]")
        redacted = redacted[: f.start] + placeholder + redacted[f.end :]

    deduped.sort(key=lambda f: f.start)
    return RedactionResult(original=text, redacted=redacted, findings=deduped)


def redact_to_json(text: str, min_confidence: float = 0.60) -> str:
    """Return JSON string with redacted text and a summary of findings."""
    r = redact(text, min_confidence)
    return json.dumps(
        {
            "redacted": r.redacted,
            "summary": r.summary(),
            "findings": [
                {
                    "category": f.category,
                    "label": f.label,
                    "confidence": f.confidence,
                    "original_length": len(f.original),
                }
                for f in r.findings
            ],
        },
        indent=2,
    )


def main() -> None:
    if len(sys.argv) > 1:
        path = sys.argv[1]
        text = sys.stdin.read() if path == "-" else open(path).read()
    else:
        text = sys.stdin.read()

    print(redact_to_json(text))


if __name__ == "__main__":
    main()
