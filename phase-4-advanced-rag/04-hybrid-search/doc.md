# 04 — Hybrid Search

## Problem

Dense embeddings (Phase 0 Topic 05) represent *meaning* — they're excellent at matching
"how do I get my money back" to a document about refunds even though no words overlap.
That strength is also a weakness: an exact token like an error code, a SKU, or an
acronym doesn't carry much "meaning" on its own, so it barely moves the embedding.
`ERR_RL429` and `ERR_RL500` can end up nearly indistinguishable in embedding space, even
though a keyword search would tell them apart instantly.

## Concept

**BM25** is a classic keyword/sparse-retrieval algorithm (term-frequency based, no
embeddings involved) — it scores documents by how well their exact tokens match the
query's exact tokens. It's bad at synonyms and paraphrase, but excellent at exact terms.

**Hybrid search** runs BM25 (keyword) and dense vector search *in parallel* and fuses
their ranked results, so a query gets the benefit of both: exact-term precision from
BM25, semantic recall from embeddings.

```text
query ──┬──> BM25 (keyword)  ────┐
        │                        ├──> fuse (Reciprocal Rank Fusion) ──> merged ranking
        └──> vector (semantic) ──┘
```

`EnsembleRetriever` runs the fusion automatically — give it a list of retrievers and
weights:

```python
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 3

vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5]
)
docs = hybrid_retriever.invoke(query)
```

Internally, `EnsembleRetriever` merges the ranked lists with **Reciprocal Rank Fusion
(RRF)** — a document's fused score is the (weighted) sum of `1 / (rank + c)` across each
retriever's list, so a document ranked highly by *either* retriever scores well, without
needing the two retrievers' raw scores to be on comparable scales (BM25 scores and
cosine distances aren't).

A manual alternative (no `EnsembleRetriever`) is to just run both retrievers yourself and
combine the results with the same RRF formula — useful if you need to see exactly what's
happening or fuse retrievers `EnsembleRetriever` doesn't support directly.

## Minimal code

`code.py` adds a Nimbus support ticket that references an exact error code
(`ERR_RL429`) to the corpus, then compares three retrievers on the query
`"How do I fix ERR_RL429?"`: BM25 alone, vector search alone, and the `EnsembleRetriever`
hybrid — showing vector-only search ranking the exact-code document lower than BM25 does,
and the hybrid combining both signals.

## Production notes

Project A (Research Paper RAG) is built on hybrid search + reranking (Topic 03) — exact
citation keys, author names, and section numbers behave like the error code here: dense
search alone under-serves them. Needs `rank_bm25` (BM25Retriever's scoring backend) and
`langchain-community` (where `BM25Retriever` currently lives) — see doc.md's final report
in this phase for exact package names, since neither is in `requirements.txt` yet.

## Debugging

- BM25 misses an exact-code match you'd expect it to find → check `preprocess_func`;
  the default tokenizer lowercases and splits on whitespace/punctuation, which can split
  a code like `ERR_RL429` in unexpected ways depending on formatting.
- Hybrid results look identical to vector-only → weights are skewed too far toward the
  vector retriever (e.g. `weights=[0.1, 0.9]`); start at `[0.5, 0.5]` and tune from there.
- `BM25Retriever` import fails → it lives in `langchain_community`, not `langchain` or
  `langchain_classic` — install `langchain-community` separately.

## Mini challenge

Add a second exact-code document (`ERR_RL500`) to the corpus and re-run the query for
`ERR_RL429` — confirm BM25 (and the hybrid) correctly distinguish the two codes while
noting how close their embeddings likely are.
