# 06 — Vector Store Integration Pattern

## Problem

Phase 0 Topic 06 used Qdrant's low-level client directly, with Qdrant-specific method
names (`client.upsert`, `client.query_points`). If every part of your app calls those
specific methods, switching to FAISS or another store later means rewriting every call
site — the exact problem Topic 01 solved for models, now for vector stores.

## Concept

LangChain's `VectorStore` base class standardizes the interface across every backend:

```python
vector_store.add_documents(documents)                 # ingest
vector_store.similarity_search(query, k=4)              # retrieve
vector_store.similarity_search_with_score(query, k=4)    # retrieve + relevance scores
retriever = vector_store.as_retriever()                 # Retriever interface (Phase 3)
```

Every backend — `QdrantVectorStore`, `FAISS`, `PineconeVectorStore`, `PGVector` — exposes
this same surface, constructed slightly differently (local path vs. connection string vs.
API key) but used identically afterward:

```python
from langchain_qdrant import QdrantVectorStore
from langchain_community.vectorstores import FAISS

qdrant_store = QdrantVectorStore.from_documents(
    documents, embedding=embeddings, location=":memory:", collection_name="demo"
)
faiss_store  = FAISS.from_documents(documents, embedding=embeddings)

# identical calls from here on, regardless of which store `store` is:
qdrant_store.similarity_search("query", k=2)
faiss_store.similarity_search("query", k=2)
```

This is what makes Topic 07's "choosing a vector database" a genuinely low-risk decision
— swapping backends later is a construction-line change, not an application rewrite,
exactly like swapping model providers in Topic 01.

## Minimal code

`code.py` embeds the same small document set into both Qdrant and FAISS (both local, no
extra infra) using the exact same `.from_documents(...)` / `.similarity_search(...)`
calls, printing results from each side by side to make the interface parity concrete.

## Production notes

Prefer `.as_retriever()` over calling `similarity_search` directly once you reach Phase
3 — retrievers compose with the rest of LangChain's chain/agent machinery, while a raw
vector store doesn't.

## Debugging

- Results differ meaningfully between two stores on the identical query → check both
  are using the *same* embedding model — different embedding models are not
  cross-comparable (Phase 0 Topic 05).
- `similarity_search_with_score` scores aren't comparable across backends → different
  stores use different distance metrics (cosine vs. L2 vs. dot product) by default;
  compare rank order, not raw scores, across backends.

## Mini challenge

Add `PineconeVectorStore` (via `langchain-pinecone`, using Pinecone's free tier) as a
third backend and confirm the same calls work unchanged.
