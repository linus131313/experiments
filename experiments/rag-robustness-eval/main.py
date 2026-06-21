"""RAG robustness evaluation - measure recall@k under corpus noise."""

from corpus import DOCUMENTS, QUERIES
from noise import char_noise, word_drop, truncate
from retriever import TFIDFRetriever, mean_recall_at_k

K = 5

# Noise severity levels (0 = clean, higher = more noise)
NOISE_LEVELS = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5]


def build_and_eval(noisy_docs: dict[str, str]) -> float:
    r = TFIDFRetriever()
    r.index(noisy_docs)
    return mean_recall_at_k(r, QUERIES, k=K)


def run_char_noise() -> list[tuple[float, float]]:
    return [
        (lvl, build_and_eval({k: char_noise(v, lvl) for k, v in DOCUMENTS.items()}))
        for lvl in NOISE_LEVELS
    ]


def run_word_drop() -> list[tuple[float, float]]:
    return [
        (lvl, build_and_eval({k: word_drop(v, lvl) for k, v in DOCUMENTS.items()}))
        for lvl in NOISE_LEVELS
    ]


def run_truncate() -> list[tuple[float, float]]:
    # fraction = 1 - level so that level 0 = full doc, level 0.5 = half doc
    return [
        (
            lvl,
            build_and_eval(
                {k: truncate(v, max(0.05, 1.0 - lvl)) for k, v in DOCUMENTS.items()}
            ),
        )
        for lvl in NOISE_LEVELS
    ]


def main() -> None:
    char_res = run_char_noise()
    word_res = run_word_drop()
    trunc_res = run_truncate()

    print(f"RAG Robustness Evaluation  (Recall@{K})\n")
    header = f"{'Noise level':>12}  {'Char noise':>12}  {'Word drop':>12}  {'Truncate':>12}"
    print(header)
    print("-" * len(header))

    for i, lvl in enumerate(NOISE_LEVELS):
        trunc_note = f" (keep {(1.0 - lvl) * 100:.0f}%)" if lvl > 0 else "         "
        print(
            f"{lvl:>12.2f}  {char_res[i][1]:>12.3f}  {word_res[i][1]:>12.3f}  "
            f"{trunc_res[i][1]:>12.3f}{trunc_note}"
        )

    baseline = char_res[0][1]
    print(f"\nBaseline recall@{K}: {baseline:.3f}")
    for label, results in [("char noise", char_res), ("word drop", word_res), ("truncate", trunc_res)]:
        worst = results[-1][1]
        print(f"  {label} at level 0.5: {worst:.3f}  (delta {worst - baseline:+.3f})")


if __name__ == "__main__":
    main()
