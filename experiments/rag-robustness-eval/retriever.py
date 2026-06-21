"""TF-IDF retriever and recall@k metrics."""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TFIDFRetriever:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.doc_ids: list[str] = []
        self.doc_matrix = None

    def index(self, documents: dict[str, str]) -> None:
        """Build the TF-IDF index from {doc_id: text}."""
        self.doc_ids = list(documents.keys())
        texts = list(documents.values())
        self.doc_matrix = self.vectorizer.fit_transform(texts)

    def retrieve(self, query: str, k: int = 5) -> list[str]:
        """Return doc_ids of the top-k most similar documents."""
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.doc_matrix)[0]
        top_k_idx = np.argsort(scores)[::-1][:k]
        return [self.doc_ids[i] for i in top_k_idx]


def recall_at_k(retrieved: list[str], relevant: list[str]) -> float:
    """Fraction of relevant documents found in the retrieved list."""
    if not relevant:
        return 0.0
    hits = sum(1 for r in relevant if r in retrieved)
    return hits / len(relevant)


def mean_recall_at_k(
    retriever: TFIDFRetriever, queries: list[dict], k: int = 5
) -> float:
    """Average recall@k across all queries."""
    scores = [
        recall_at_k(retriever.retrieve(q["text"], k=k), q["relevant"])
        for q in queries
    ]
    return sum(scores) / len(scores)
