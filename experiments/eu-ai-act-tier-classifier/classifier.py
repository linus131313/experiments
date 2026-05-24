#!/usr/bin/env python3
"""Rule-based EU AI Act risk tier classifier."""

import sys
from dataclasses import dataclass, field


@dataclass
class Classification:
    tier: str
    confidence: str  # high / medium / low
    matched_rules: list = field(default_factory=list)
    citations: list = field(default_factory=list)
    summary: str = ""


# Rules checked in priority order: Unacceptable > High > Limited > Minimal.
# Each rule has 'keywords' (required) and optional 'context_keywords' (all must
# appear alongside at least one keyword for the rule to fire).

UNACCEPTABLE_RULES = [
    {
        "keywords": ["social scor", "social credit", "citizen score", "trustworthiness score"],
        "description": "Social scoring of individuals by public authorities",
        "article": "Art. 5(1)(c)",
    },
    {
        "keywords": ["subliminal", "subliminal technique"],
        "description": "Subliminal manipulation of behaviour causing harm",
        "article": "Art. 5(1)(a)",
    },
    {
        "keywords": ["real-time biometric", "live facial recognition", "real time remote biometric"],
        "description": "Real-time remote biometric identification in public spaces for law enforcement",
        "article": "Art. 5(1)(h)",
    },
    {
        "keywords": ["predictive policing", "predict crime location", "predict criminal behaviour"],
        "description": "Predictive policing based solely on profiling or personality traits",
        "article": "Art. 5(1)(d)",
    },
    {
        "keywords": ["emotion recogni", "emotion detection", "emotional state"],
        "context_keywords": ["workplace", "school", "classroom", "university", "educational"],
        "description": "Emotion recognition in workplaces or educational institutions",
        "article": "Art. 5(1)(f)",
    },
    {
        "keywords": ["biometric categoris", "biometric classif", "infer race", "infer ethnicity",
                     "infer religion", "infer sexual orientation", "infer political"],
        "description": "Biometric categorisation inferring sensitive characteristics",
        "article": "Art. 5(1)(g)",
    },
    {
        "keywords": ["exploit vulnerabilit", "exploit vulnerability", "exploit weakness",
                     "manipulate elderly", "manipulate children", "manipulate disabled"],
        "description": "Exploitation of vulnerabilities of specific groups causing harm",
        "article": "Art. 5(1)(b)",
    },
]

HIGH_RISK_RULES = [
    {
        "keywords": ["critical infrastructure", "electricity grid", "power grid",
                     "water supply", "transport safety", "gas supply"],
        "description": "Safety of critical infrastructure",
        "article": "Art. 6(2), Annex III(2)",
    },
    {
        "keywords": ["education", "school", "university", "vocational", "exam",
                     "student admission", "academic assessment", "grading students"],
        "description": "AI in education and vocational training",
        "article": "Art. 6(2), Annex III(3)",
    },
    {
        "keywords": ["job applicant", "hiring", "recruit", "employment decision",
                     "worker monitor", "promotion decision", "termination decision",
                     "workforce management"],
        "description": "AI in employment and workers management",
        "article": "Art. 6(2), Annex III(4)",
    },
    {
        "keywords": ["creditworthiness", "credit scoring", "loan decision",
                     "insurance eligibility", "benefit entitlement", "essential service access"],
        "description": "Access to essential private and public services",
        "article": "Art. 6(2), Annex III(5)",
    },
    {
        "keywords": ["law enforcement", "policing", "criminal suspect", "forensic",
                     "evidence assessment", "crime investigation", "risk assessment offender"],
        "description": "Law enforcement applications",
        "article": "Art. 6(2), Annex III(6)",
    },
    {
        "keywords": ["migration", "border control", "asylum", "visa assessment", "immigration decision"],
        "description": "Migration, asylum, and border control",
        "article": "Art. 6(2), Annex III(7)",
    },
    {
        "keywords": ["judicial decision", "court ruling", "legal dispute", "administration of justice",
                     "sentencing", "legal proceeding"],
        "description": "Administration of justice and democratic processes",
        "article": "Art. 6(2), Annex III(8)",
    },
    {
        "keywords": ["medical diagnosis", "clinical decision", "patient triage", "diagnostic imaging",
                     "disease detection", "medical device safety", "surgical robot"],
        "description": "Safety component in medical devices or high-risk health AI",
        "article": "Art. 6(2), Annex III(1) / Annex I",
    },
    {
        "keywords": ["autonomous vehicle", "self-driving", "aviation safety",
                     "railway safety", "maritime safety"],
        "description": "Safety component in transport systems",
        "article": "Art. 6(2), Annex III(2)",
    },
]

LIMITED_RISK_RULES = [
    {
        "keywords": ["chatbot", "conversational ai", "virtual assistant", "dialogue system",
                     "chat assistant"],
        "description": "Chatbots / conversational AI - transparency obligation",
        "article": "Art. 50(1)",
    },
    {
        "keywords": ["deepfake", "deep fake", "synthetic video", "synthetic audio",
                     "ai-generated image", "ai generated image", "synthetic media"],
        "description": "AI-generated or manipulated content (deep fake / synthetic media)",
        "article": "Art. 50(4)",
    },
    {
        "keywords": ["emotion recogni", "emotion detection", "emotional state"],
        "description": "Emotion recognition systems - transparency obligation",
        "article": "Art. 50(3)",
    },
    {
        "keywords": ["recommendation system", "content recommendation", "personalised feed",
                     "personalisation engine"],
        "description": "Content recommendation and personalisation - transparency obligation",
        "article": "Art. 50",
    },
]


def _find_keywords(text: str, keywords: list) -> list:
    lower = text.lower()
    return [kw for kw in keywords if kw.lower() in lower]


def classify(description: str) -> Classification:
    """Return the EU AI Act risk tier for the given use-case description."""
    text = description.strip()

    # 1. Unacceptable Risk (prohibited)
    for rule in UNACCEPTABLE_RULES:
        hits = _find_keywords(text, rule["keywords"])
        if not hits:
            continue
        if "context_keywords" in rule:
            if not _find_keywords(text, rule["context_keywords"]):
                continue
        return Classification(
            tier="Unacceptable",
            confidence="high" if len(hits) >= 2 else "medium",
            matched_rules=[rule["description"]],
            citations=[rule["article"]],
            summary=(
                "This use case appears to be prohibited under the EU AI Act. "
                f"Matched rule: {rule['description']}. "
                f"Reference: {rule['article']}."
            ),
        )

    # 2. High Risk
    high_matches = [r for r in HIGH_RISK_RULES if _find_keywords(text, r["keywords"])]
    if high_matches:
        descs = [r["description"] for r in high_matches]
        citations = list(dict.fromkeys(r["article"] for r in high_matches))
        return Classification(
            tier="High",
            confidence="high" if len(high_matches) >= 2 else "medium",
            matched_rules=descs,
            citations=citations,
            summary=(
                "This use case is likely High Risk under the EU AI Act "
                "(Art. 6 and Annex III). Conformity assessment, registration, "
                "and ongoing monitoring are required. "
                f"Matched: {', '.join(descs[:2])}."
            ),
        )

    # 3. Limited Risk
    limited_matches = [r for r in LIMITED_RISK_RULES if _find_keywords(text, r["keywords"])]
    if limited_matches:
        descs = [r["description"] for r in limited_matches]
        citations = list(dict.fromkeys(r["article"] for r in limited_matches))
        return Classification(
            tier="Limited",
            confidence="high" if len(limited_matches) >= 2 else "medium",
            matched_rules=descs,
            citations=citations,
            summary=(
                "This use case falls under Limited Risk - transparency obligations apply. "
                f"Users must be informed they are interacting with AI. "
                f"Matched: {', '.join(descs)}."
            ),
        )

    # 4. Minimal Risk
    return Classification(
        tier="Minimal",
        confidence="low",
        matched_rules=[],
        citations=["No specific obligations under Art. 5-50"],
        summary=(
            "No specific EU AI Act obligations identified for this use case. "
            "Good practices apply; monitor regulatory updates."
        ),
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python classifier.py '<use-case description>'")
        print("       echo 'description' | python classifier.py -")
        sys.exit(1)

    if sys.argv[1] == "-":
        description = sys.stdin.read()
    else:
        description = " ".join(sys.argv[1:])

    result = classify(description)

    TIER_COLORS = {
        "Unacceptable": "\033[91m",
        "High":         "\033[93m",
        "Limited":      "\033[94m",
        "Minimal":      "\033[92m",
    }
    RESET = "\033[0m"
    color = TIER_COLORS.get(result.tier, "")

    print(f"\nRisk Tier:  {color}{result.tier}{RESET}  (confidence: {result.confidence})")
    print(f"Summary:    {result.summary}")
    print(f"Citations:  {', '.join(result.citations)}")
    if result.matched_rules:
        print("Matched rules:")
        for rule in result.matched_rules:
            print(f"  - {rule}")
    print()


if __name__ == "__main__":
    main()
