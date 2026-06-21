# rag-robustness-eval

Inject controlled noise into a retrieval corpus and measure Recall@5 degradation
on a toy dataset. Three noise types are tested: character-level corruption,
word-level deletion, and document truncation.

## What it does

Builds a 20-document toy corpus of programming-topic descriptions (Python,
Git, Docker, SQL, etc.) with 10 labeled queries. A TF-IDF retriever is indexed
on progressively noisier versions of the corpus and Recall@5 is reported at
each noise level.

Noise types:
- **char noise** - replaces random alphabetic characters with random letters
- **word drop** - randomly deletes words at a given rate
- **truncate** - keeps only the first N% of each document

## How to run

```bash
pip install -r requirements.txt
python main.py
python -m pytest test_rag_robustness.py -v
```

## Findings

```
RAG Robustness Evaluation  (Recall@5)

 Noise level    Char noise     Word drop      Truncate
------------------------------------------------------
        0.00         1.000         1.000         1.000
        0.05         0.950         1.000         1.000
        0.10         0.950         1.000         1.000
        0.20         0.750         1.000         1.000
        0.30         0.550         1.000         1.000
        0.50         0.550         1.000         1.000
```

Extended word-drop sweep:

| Drop rate | Recall@5 |
|-----------|----------|
| 50%       | 1.000    |
| 70%       | 0.700    |
| 85%       | 0.400    |
| 95%       | 0.400    |

Extended truncation sweep (keeping 5-30% of each document): Recall@5 stays at
1.000 even at 5% retention.

**Key observations:**

1. **Character noise is the most damaging noise type for TF-IDF.** At 20% char
   corruption, recall drops to 0.75; at 50% it drops to 0.55. Each corrupted
   character converts an in-vocabulary token into an OOV token, destroying the
   term-matching signal that TF-IDF relies on. This matters for OCR-heavy RAG
   pipelines (scanned PDFs, handwritten notes).

2. **Word deletion requires extreme rates to hurt recall.** At 50% drop rate,
   recall stays at 1.0 because the surviving half of each document still
   contains all the distinguishing content words. Retrieval degrades only above
   70% deletion. This means aggressive summarisation or bullet-point extraction
   of source documents is unlikely to harm sparse retrieval.

3. **Truncation barely affects recall.** Even retaining only 5% of each
   document (roughly one sentence) Recall@5 remains 1.0. The first sentence of
   each document in this corpus contains the key distinguishing terms, so
   truncation is essentially just aggressive summarisation.

4. **Sparse retrieval (TF-IDF) is brittle to character-level noise but
   resilient to content removal.** This asymmetry suggests that text
   normalisation and spell-checking are higher-value pre-processing steps than
   deduplication or length reduction for sparse retrieval systems.

5. **The toy corpus is too clean and too topically distinct.** Documents do not
   share vocabulary across topics, so even a fragment retrieves the correct
   document. A realistic corpus with overlapping vocabulary would show earlier
   degradation across all noise types.

## Scope

- 20 documents, 10 queries, TF-IDF with cosine similarity
- Three noise types: char substitution, word deletion, truncation
- Recall@5 as the single metric

## Out of scope

- Dense retrieval (sentence-transformers, OpenAI embeddings) - char noise
  would likely hurt less there since embeddings interpolate over nearby tokens
- BM25 comparison
- Noisy queries (vs noisy documents)
- Realistic multi-topic corpora where documents share vocabulary
- Hybrid retrieval pipelines
