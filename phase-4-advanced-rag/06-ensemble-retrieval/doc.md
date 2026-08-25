# 06 — Ensemble Retrieval

## Problem

Topic 04 solved one specific mismatch — keyword vs. semantic — by combining exactly two
retrievers (BM25 + vector). But "combine several retrievers and merge their rankings" is
a more general pattern than that one pairing. You might want to combine a vector
retriever tuned for short precise chunks with one tuned for long context-rich chunks
(Topic 05's parents), or a retriever scoped to one data source with one scoped to
another (this is exactly what Project C's multi-department knowledge base needs). None
of these pairings are "keyword vs. semantic" — they're still worth fusing.

## Concept

**This topic and Topic 04 use the same mechanism** — `EnsembleRetriever` and Reciprocal
Rank Fusion — the difference is framing, not code. Topic 04 = one named technique
("hybrid search," specifically BM25 + dense). Topic 06 = the general pattern of fusing
*any* N retrievers, whatever they are, with independent weights.

```python
from langchain_classic.retrievers import EnsembleRetriever

ensemble = EnsembleRetriever(
    retrievers=[bm25_retriever, small_chunk_retriever, large_chunk_retriever],
    weights=[0.3, 0.3, 0.4],   # must sum to 1.0; tune per retriever's reliability
)
docs = ensemble.invoke(query)
```

`EnsembleRetriever` fuses ranked lists with Reciprocal Rank Fusion regardless of what
produced each list — a BM25 score, a cosine distance, and a metadata-filtered vector
search are all just "a ranking" by the time RRF sees them, which is what makes this
generalize past the keyword/semantic pairing.

```text
   retriever A (BM25)        retriever B (small chunks)     retriever C (large chunks)
        │  ranked list             │  ranked list                 │  ranked list
        └──────────────┬───────────┴───────────────┬───────────────┘
                        ▼                           ▼
                        Reciprocal Rank Fusion (weighted)
                                    │
                                    ▼
                            one merged ranking
```

## Minimal code

`code.py` builds three retrievers over the same Nimbus runbook from Topic 05 — BM25,
a small-chunk vector retriever, and a large-chunk ("parent-sized") vector retriever —
and fuses all three with `EnsembleRetriever`, comparing the fused ranking against each
retriever alone for a query none of them individually rank ideally.

## Production notes

Project C (Multi-Document Enterprise RAG) is built on this pattern: one retriever per
data source or department (each possibly with its own chunking/embedding choices),
fused with `EnsembleRetriever`, then filtered by Topic 07's relevance grading and
checked with Topic 08's groundedness eval before an answer reaches a user — ensemble
retrieval is the "gather candidates from everywhere" stage of that pipeline.

## Debugging

- One retriever dominates the fused ranking regardless of weight → check that
  retriever isn't returning a much longer or much shorter list than the others; RRF's
  `1/(rank+c)` formula means a retriever contributing more ranked results has more
  chances to score well unless list lengths are comparable.
- Fused results contain obvious duplicates → confirm the underlying documents share a
  consistent `id_key`/content identity across retrievers; `EnsembleRetriever` dedupes by
  document content by default, but only if the content strings actually match exactly.

## Mini challenge

Drop one retriever from the ensemble (e.g. remove the large-chunk retriever) and compare
the fused ranking with two retrievers vs. three — confirm more retrievers isn't always
strictly better once redundant retrievers start diluting a strong signal from the others.
