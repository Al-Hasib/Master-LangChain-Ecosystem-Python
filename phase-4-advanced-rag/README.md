# Phase 4 — Advanced RAG

**Status:** ✅ Fully built — every topic has doc.md and code.py.

**Premise for this phase:** naive top-k similarity search breaks in predictable ways
(ambiguous queries, irrelevant chunks, redundant context). Each topic fixes one specific
failure mode.

## Topics

01. [Naive RAG vs Production RAG](01-naive-rag-vs-production-rag/doc.md) — cataloguing the failure modes Phase 3's pipeline has, which motivate every topic below.
02. [Query Transformation Techniques](02-query-transformation-techniques/doc.md) — query rewriting, multi-query retrieval, and HyDE (hypothetical document embeddings) to fix ambiguous/underspecified queries.
03. [Contextual Compression & Reranking](03-contextual-compression-and-reranking/doc.md) — trimming retrieved chunks to what's relevant, reordering by a cross-encoder reranker.
04. [Hybrid Search](04-hybrid-search/doc.md) — combining keyword (BM25) and semantic search for queries dense retrieval alone misses.
05. [Parent-Document & Multi-Vector Retrieval](05-parent-document-and-multi-vector-retrieval/doc.md) — retrieving small chunks for precision, returning larger parent context for generation.
06. [Ensemble Retrieval](06-ensemble-retrieval/doc.md) — combining multiple retrievers/strategies and merging results.
07. [Document Relevance Grading & Self-Correction](07-document-relevance-grading-and-self-correction/doc.md) — an LLM grades retrieved docs before generation; re-retrieve or re-query on a bad grade.
08. [Retrieval & Groundedness Evaluation](08-retrieval-and-groundedness-evaluation/doc.md) — measuring whether retrieved context actually supports the generated answer.

## Running the examples

```bash
pip install -r ../requirements.txt
pip install langchain-classic langchain-community rank_bm25   # not yet pinned in requirements.txt - see topic docs
cp ../.env.example ../.env   # fill in OPENAI_API_KEY at minimum
python 01-naive-rag-vs-production-rag/code.py
```

## Phase projects

- **Project A — Research Paper RAG** (hybrid search + reranking)
- **Project B — Documentation RAG** (parent-document retrieval, freshness-aware)
- **Project C — Multi-Document Enterprise RAG** (ensemble retrieval + grading + groundedness checks)
