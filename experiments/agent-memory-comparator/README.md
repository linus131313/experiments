# agent-memory-comparator

Run the same toy retrieval workload against three in-process memory backends and
compare retrieval quality and context-window cost.

## What it does

A fixed corpus of 20 short documents about Python, Java, and Rust is indexed by
each backend. Eight natural-language queries are issued against all three backends
(k=3), and the results are scored for Precision@3, Recall@3, and total characters
retrieved (a proxy for LLM token cost).

### Backends

| Backend | Strategy |
|---|---|
| **Vector (TF-IDF)** | Cosine similarity over TF-IDF document vectors; handles paraphrase. |
| **Graph (NetworkX)** | Bipartite doc-tag graph; scores docs by tag-word overlap with the query. |
| **KV (inverted index)** | Inverted tag index; scores docs by count of matching tags. |

## How to run

```bash
pip install -r requirements.txt
python main.py          # print comparison table
python -m pytest        # run 5 unit tests
```

## Findings

```
Backend                      P@k     R@k   Chars/query
------------------------------------------------------
Vector (TF-IDF)            0.500   0.500           433
Graph (NetworkX)           0.583   0.583           458
KV (inverted index)        0.583   0.583           458
```

- Graph and KV tie on this corpus because the concept tags are well-matched to the
  query vocabulary, so the two traversal strategies produce the same ranking.
- Vector scores lower because TF-IDF privileges exact term matches; queries that
  use different words than the document (e.g. "parallelism" vs "GIL") get
  penalised.
- Chars/query is similar across backends because all three return exactly k=3 docs
  per query. The difference between backends would widen with a larger or noisier
  corpus where some backends retrieve zero results for certain queries.
- Graph's secondary strength (not visible at k=3 here) is surfacing
  cross-cutting documents that share multiple concept nodes with a query, which
  becomes relevant when the corpus has richer inter-document relationships.

## Scope

- No LLM calls; all retrieval is local and deterministic.
- Token cost is approximated by character count (1 token ~ 4 chars).
- Tags are manually annotated; a real system would derive them automatically
  (NER, embedding clusters, etc.).

## Out of scope

- Embedding-based vector search (e.g. sentence-transformers, FAISS).
- Persistent storage (Redis, Neo4j, Weaviate).
- Hybrid retrieval combining multiple backends.
- Automatic tag extraction from document text.
