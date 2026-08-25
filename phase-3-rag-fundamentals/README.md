# Phase 3 — RAG Fundamentals

**Status:** 🗒️ Topic list only — ask for this phase by name to have it fully built out.

**Frame this phase around the current LangChain retrieval model:** loaders → splitters →
embeddings → vector stores → retrievers, building toward "2-step RAG" as the baseline
before Phase 4 complicates it.

## Topics

01. **RAG Architecture Overview** — the 2-step RAG pattern: retrieve, then generate.
02. **Document Loaders & Document Objects** — turning raw files into `Document`s with `page_content` + `metadata`.
03. **Text Splitting & Chunking Strategies** — chunk size, overlap, recursive vs semantic splitting, and why chunking quality drives retrieval quality.
04. **Embeddings & Vector Stores** — embedding models, storing vectors, similarity metrics.
05. **Retrievers & Similarity Search** — the `Retriever` interface, top-k, score thresholds.
06. **Metadata Filtering** — narrowing retrieval by source, date, tags before/alongside similarity search.
07. **Building a Basic RAG Pipeline** — wiring loader → splitter → embeddings → store → retriever → prompt → LLM, plus returning sources/citations.
08. **RAG Evaluation Basics** — precision/recall of retrieval, answer relevance, first look at LangSmith datasets.

## Phase project

**PDF Knowledge Assistant** — a Q&A app over a folder of PDFs with cited sources.

```text
PDF → Loader → Splitter → Embeddings → Vector DB → Retriever → LLM → Answer + Sources
```
