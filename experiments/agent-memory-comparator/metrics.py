"""Retrieval quality metrics and token-cost proxy."""

from __future__ import annotations


def precision_at_k(retrieved: list[str], relevant: list[str]) -> float:
    if not retrieved:
        return 0.0
    return sum(1 for r in retrieved if r in relevant) / len(retrieved)


def recall_at_k(retrieved: list[str], relevant: list[str]) -> float:
    if not relevant:
        return 0.0
    return sum(1 for r in retrieved if r in relevant) / len(relevant)


def context_chars(retrieved: list[str], corpus: dict[str, dict]) -> int:
    """Total characters in retrieved items - proxy for LLM context token cost."""
    return sum(len(corpus[doc_id]["content"]) for doc_id in retrieved if doc_id in corpus)


def mean_metrics(
    backend: object,
    queries: list[dict],
    corpus: dict[str, dict],
    k: int = 3,
) -> dict[str, float]:
    p_scores, r_scores, char_costs = [], [], []
    for q in queries:
        retrieved = backend.query(q["question"], k=k)
        p_scores.append(precision_at_k(retrieved, q["relevant"]))
        r_scores.append(recall_at_k(retrieved, q["relevant"]))
        char_costs.append(context_chars(retrieved, corpus))
    return {
        "precision_at_k": sum(p_scores) / len(p_scores),
        "recall_at_k": sum(r_scores) / len(r_scores),
        "mean_context_chars": sum(char_costs) / len(char_costs),
    }
