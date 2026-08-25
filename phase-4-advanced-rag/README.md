# Phase 4 — Advanced RAG

**Status:** 🗒️ Topic list only — ask for this phase by name to have it fully built out.

**Premise for this phase:** naive top-k similarity search breaks in predictable ways
(ambiguous queries, irrelevant chunks, redundant context). Each topic fixes one specific
failure mode.

## Topics

01. **Naive RAG vs Production RAG** — cataloguing the failure modes Phase 3's pipeline has, which motivate every topic below.
02. **Query Transformation Techniques** — query rewriting, multi-query retrieval, and HyDE (hypothetical document embeddings) to fix ambiguous/underspecified queries.
03. **Contextual Compression & Reranking** — trimming retrieved chunks to what's relevant, reordering by a cross-encoder reranker.
04. **Hybrid Search** — combining keyword (BM25) and semantic search for queries dense retrieval alone misses.
05. **Parent-Document & Multi-Vector Retrieval** — retrieving small chunks for precision, returning larger parent context for generation.
06. **Ensemble Retrieval** — combining multiple retrievers/strategies and merging results.
07. **Document Relevance Grading & Self-Correction** — an LLM grades retrieved docs before generation; re-retrieve or re-query on a bad grade.
08. **Retrieval & Groundedness Evaluation** — measuring whether retrieved context actually supports the generated answer.

## Phase projects

- **Project A — Research Paper RAG** (hybrid search + reranking)
- **Project B — Documentation RAG** (parent-document retrieval, freshness-aware)
- **Project C — Multi-Document Enterprise RAG** (ensemble retrieval + grading + groundedness checks)
