# 06 — Vector Databases Explained

## Problem

Topic 05 computed similarity between a query and 5 sentences by hand — comparing every
vector to every other one. That's `O(n)` per query and falls over well before a million
documents. Vector databases exist to make "find the most similar vectors" fast and
persistent at scale.

## Concept

A **vector database** (or vector store) does three things a plain list of vectors
doesn't:

1. **Persistence** — store vectors + their source text + metadata durably, not just in
   memory for one script run.
2. **Fast approximate search** — index structures (e.g. HNSW) that find near-neighbors
   in roughly logarithmic time instead of scanning every vector.
3. **Filtering** — combine similarity search with metadata filters (e.g. "only
   documents where `source = 'handbook.pdf'`").

Two families you'll use in this course:
- **Local/embedded** (Chroma, FAISS) — run in-process or as a local server, zero infra,
  great for development and small-to-medium datasets.
- **Managed/distributed** (Pinecone, Qdrant, pgvector-on-Postgres) — built for
  production scale, often add hybrid search and richer filtering.

```text
Document -> Embedding model -> vector ---\
                                            > stored in Vector DB (indexed)
Query    -> Embedding model -> vector ---/          |
                                                       v
                                     approximate nearest-neighbor search
                                                       v
                                            top-k most similar documents
```

This whole pipeline — embed once at ingest time, embed again per query, search — is
exactly what Phase 3's "RAG" pattern automates with LangChain's `VectorStore` and
`Retriever` abstractions.

## Minimal code

`code.py` uses Chroma (local, no server needed) to store the same 5 sentences from
Topic 05 with metadata, then runs a similarity search — showing the same ranking Topic
05 computed by hand, now via a real vector database in ~10 lines.

## Production notes

Chroma/FAISS are fine through early production; move to a managed/distributed store
when you need: multi-machine scale, high write throughput, built-in hybrid search, or
zero-ops hosting. Choosing one is covered properly in Phase 2's "Choosing a Vector
Database" topic.

## Debugging

- Search returns nothing → check the collection actually has documents added (a common
  first-run mistake is querying an empty/newly-created collection).
- Search returns irrelevant results → verify the same embedding model was used for both
  ingestion and querying.

## Mini challenge

Add metadata (`{"topic": "animals"}` / `{"topic": "finance"}`) to each sentence and
filter the search to only the `"animals"` topic before ranking.
