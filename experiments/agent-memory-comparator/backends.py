"""Three memory backends: Vector (TF-IDF), Graph (NetworkX), KV (inverted index)."""

from __future__ import annotations

import re
from collections import defaultdict

import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_STOPWORDS = {
    "the", "a", "an", "and", "or", "is", "are", "of", "in", "to", "for",
    "with", "how", "what", "does", "do", "by", "its", "including", "via",
    "as", "at", "be", "can", "it", "on", "without",
}


def _tokenize(text: str) -> set[str]:
    return {
        w for w in re.findall(r"[a-z]+", text.lower())
        if w not in _STOPWORDS and len(w) > 2
    }


class VectorBackend:
    """TF-IDF cosine similarity retrieval."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._vectorizer = TfidfVectorizer()
        self._matrix = None

    def build(self, corpus: dict[str, dict]) -> None:
        self._ids = list(corpus.keys())
        texts = [item["content"] for item in corpus.values()]
        self._matrix = self._vectorizer.fit_transform(texts)

    def query(self, text: str, k: int = 3) -> list[str]:
        q_vec = self._vectorizer.transform([text])
        sims = cosine_similarity(q_vec, self._matrix)[0]
        top = np.argsort(sims)[::-1][:k]
        return [self._ids[i] for i in top if sims[i] > 0]


class GraphBackend:
    """NetworkX concept-graph retrieval.

    Docs and tags are nodes; edges connect each doc to its tags.
    A query scores each doc by how many of its tags share words with the query.
    """

    def __init__(self) -> None:
        self._graph: nx.Graph = nx.Graph()

    def build(self, corpus: dict[str, dict]) -> None:
        for doc_id, item in corpus.items():
            self._graph.add_node(doc_id, kind="doc")
            for tag in item["tags"]:
                self._graph.add_node(tag, kind="tag")
                self._graph.add_edge(doc_id, tag)

    def query(self, text: str, k: int = 3) -> list[str]:
        tokens = _tokenize(text)
        scores: dict[str, int] = defaultdict(int)
        for node, data in self._graph.nodes(data=True):
            if data.get("kind") == "tag" and set(node.split("-")) & tokens:
                for neighbor in self._graph.neighbors(node):
                    if self._graph.nodes[neighbor].get("kind") == "doc":
                        scores[neighbor] += 1
        return sorted(scores, key=lambda x: scores[x], reverse=True)[:k]


class KVBackend:
    """Inverted tag-index retrieval.

    Each tag maps to the list of docs that carry it.
    A query scores each doc by the number of its tags that match query tokens.
    """

    def __init__(self) -> None:
        self._index: dict[str, list[str]] = defaultdict(list)

    def build(self, corpus: dict[str, dict]) -> None:
        for doc_id, item in corpus.items():
            for tag in item["tags"]:
                self._index[tag].append(doc_id)

    def query(self, text: str, k: int = 3) -> list[str]:
        tokens = _tokenize(text)
        scores: dict[str, int] = defaultdict(int)
        for tag, doc_ids in self._index.items():
            if set(tag.split("-")) & tokens:
                for doc_id in doc_ids:
                    scores[doc_id] += 1
        return sorted(scores, key=lambda x: scores[x], reverse=True)[:k]
