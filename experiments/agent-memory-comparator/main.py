"""Agent memory comparator - benchmark vector, graph, and KV memory backends."""

from __future__ import annotations

from backends import GraphBackend, KVBackend, VectorBackend
from metrics import mean_metrics
from workload import CORPUS, QUERIES

K = 3
BACKENDS: dict[str, object] = {
    "Vector (TF-IDF)    ": VectorBackend(),
    "Graph (NetworkX)   ": GraphBackend(),
    "KV (inverted index)": KVBackend(),
}


def main() -> None:
    results = {}
    for name, backend in BACKENDS.items():
        backend.build(CORPUS)
        results[name] = mean_metrics(backend, QUERIES, CORPUS, k=K)

    n_q = len(QUERIES)
    n_d = len(CORPUS)
    print(f"Agent Memory Comparator  (k={K}, {n_q} queries, {n_d} docs)\n")

    header = f"{'Backend':<24}  {'P@k':>6}  {'R@k':>6}  {'Chars/query':>12}"
    print(header)
    print("-" * len(header))
    for name, m in results.items():
        print(
            f"{name:<24}  {m['precision_at_k']:>6.3f}  {m['recall_at_k']:>6.3f}"
            f"  {m['mean_context_chars']:>12.0f}"
        )

    print(
        "\nKey observations:"
        "\n  Vector - handles paraphrase via TF-IDF similarity."
        "\n  Graph  - concept-hop links surface cross-cutting documents."
        "\n  KV     - precise when query words match tags; brittle otherwise."
        "\n  Chars/query is a proxy for LLM context window cost."
    )


if __name__ == "__main__":
    main()
