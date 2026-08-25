# 03 — Contextual Compression & Reranking

## Problem

Topic 02's query transformations get *more* of the right documents into the candidate
set — but "in the candidate set" isn't the same as "well-ordered" or "free of noise."
Two problems remain even after retrieval improves:

1. Each retrieved chunk may contain a lot of text that isn't actually relevant to *this*
   query, diluting the context the LLM has to reason over (and costing tokens).
2. Similarity-search order (by embedding distance) isn't the same as true relevance
   order for this specific question — the 1st-ranked chunk by cosine distance is
   sometimes less useful than the 4th.

## Concept

Two complementary fixes, both applied *after* retrieval, *before* generation:

**Contextual compression** — trim each retrieved document down to only the
sentences/spans relevant to the query, instead of passing the whole chunk through.

```python
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, base_retriever=vectorstore.as_retriever()
)
docs = compression_retriever.invoke(query)  # each doc's content is now query-relevant excerpts only
```

**Reranking** — re-score a candidate set with something more precise (and more
expensive) than embedding distance, then keep only the top N by that score.

```text
similarity_search(k=8) -> 8 candidates, ranked by embedding distance
                              │  rerank (precise, expensive, only run on 8 - not the whole corpus)
                              ▼
                         top 3, ranked by true relevance
```

In production this is usually a **cross-encoder reranker** (e.g. Cohere Rerank, or a
local model like `BAAI/bge-reranker`) — a model trained specifically to score
(query, document) pairs jointly, which is more accurate than comparing two independently
computed embeddings but too slow to run over an entire corpus, which is why it only runs
on a small shortlist.

This example avoids requiring a paid Cohere key or a heavy local model download and
instead implements **LLM-as-reranker**: ask the chat model itself to score each
candidate's relevance (0–10, via structured output) and sort by that score. It's slower
and pricier per call than a real reranker, but demonstrates the *pattern* — retrieve
wide, rerank narrow, generate from the top — with zero extra infrastructure.

## Minimal code

`code.py` retrieves a wider candidate set (k=5) for a Nimbus query, then (a) runs
contextual compression to show each candidate trimmed to its relevant span, and (b) runs
the LLM-as-reranker to re-score and reorder the same candidates, printing the score-order
next to the original similarity-order so the difference is visible.

## Production notes

Real reranking APIs/models: **Cohere Rerank** (hosted, cheap, fast, purpose-built) and
local **cross-encoder** models (e.g. `sentence-transformers` cross-encoders, or
`BAAI/bge-reranker-*`) for when you can't call an external API. Both plug into the same
"retrieve wide, rerank narrow" pattern shown here — only the scoring step changes.
Project A (Research Paper RAG) is built on exactly this: hybrid search (Topic 04) for
candidate generation, reranking for precision on top of it.

## Debugging

- Compression returns an empty string for a chunk that *was* relevant → the extractor
  prompt is too strict; fall back to the original chunk when extraction is empty rather
  than silently dropping the document.
- Reranking cost/latency blows up → you're reranking too large a candidate set. Rerank a
  bounded shortlist (5–20 candidates), never the whole corpus — that's what the initial
  retrieval step is for.
- LLM-as-reranker gives inconsistent scores across runs → set `temperature=0` and use a
  structured (Pydantic) output schema rather than asking it to write a number in prose.

## Mini challenge

Run the LLM-as-reranker over a candidate set of 6–7 documents (raise `k`) instead of 5,
and see whether score quality degrades as the shortlist grows — this is exactly the
scaling limit that makes cheap cross-encoders the production default over LLM scoring.
