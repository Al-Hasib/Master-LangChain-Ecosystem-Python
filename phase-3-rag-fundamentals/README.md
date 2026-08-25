# Phase 3 — RAG Fundamentals

**Status:** ✅ Fully built — every topic has doc.md and code.py.

**Frame this phase around the current LangChain retrieval model:** loaders → splitters →
embeddings → vector stores → retrievers, building toward "2-step RAG" as the baseline
before Phase 4 complicates it.

## Topics

01. [RAG Architecture Overview](01-rag-architecture-overview/doc.md) — the 2-step RAG pattern: retrieve, then generate.
02. [Document Loaders & Document Objects](02-document-loaders-and-document-objects/doc.md) — turning raw files into `Document`s with `page_content` + `metadata`.
03. [Text Splitting & Chunking Strategies](03-text-splitting-and-chunking-strategies/doc.md) — chunk size, overlap, recursive vs semantic splitting, and why chunking quality drives retrieval quality.
04. [Embeddings & Vector Stores](04-embeddings-and-vector-stores/doc.md) — embedding models, storing vectors, similarity metrics.
05. [Retrievers & Similarity Search](05-retrievers-and-similarity-search/doc.md) — the `Retriever` interface, top-k, score thresholds.
06. [Metadata Filtering](06-metadata-filtering/doc.md) — narrowing retrieval by source, date, tags before/alongside similarity search.
07. [Building a Basic RAG Pipeline](07-building-a-basic-rag-pipeline/doc.md) — wiring loader → splitter → embeddings → store → retriever → prompt → LLM, plus returning sources/citations.
08. [RAG Evaluation Basics](08-rag-evaluation-basics/doc.md) — precision/recall of retrieval, answer relevance, first look at LangSmith datasets.

## Phase project

**PDF Knowledge Assistant** — a Q&A app over a folder of PDFs with cited sources.

```text
PDF → Loader → Splitter → Embeddings → Vector DB → Retriever → LLM → Answer + Sources
```
