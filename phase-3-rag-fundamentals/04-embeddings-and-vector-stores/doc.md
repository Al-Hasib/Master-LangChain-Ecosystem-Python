# 04 — Embeddings & Vector Stores

## Problem

Topic 03 leaves you with a pile of right-sized chunks (`list[Document]`). They're still
just text — nothing about them is searchable by *meaning* yet. Phase 0 Topics 05–06
explained *why* embeddings + vector databases make semantic search possible; this topic
is the LangChain API that actually does it to real chunks, not the 5-sentence toy
examples those topics used.

## Concept

Two objects, same ones Phase 2 Topic 06 introduced for the vector-store *interface* —
now used for their actual Phase 3 job:

```python
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")   # Phase 0 Topic 05
vector_store = QdrantVectorStore.from_documents(
    chunks, embedding=embeddings, location=":memory:", collection_name="my_collection"
)  # Phase 0 Topic 06
```

`QdrantVectorStore.from_documents` does two things in one call: embeds every chunk's
`page_content` with `embeddings`, and stores the resulting vectors alongside each
chunk's original text and `metadata` (Topic 02) in the index. `.add_documents(more)`
does the same for chunks added later, incrementally.

```text
list[Document] (chunks, Topic 03)
        │
        ▼  embeddings.embed_documents(...)     <- Phase 0 Topic 05
        ▼
[vector, vector, vector, ...]  (one per chunk, metadata + text kept alongside)
        │
        ▼  stored + indexed in Qdrant            <- Phase 0 Topic 06
        ▼
query -> embeddings.embed_query(...) -> nearest-neighbor search -> top-k Documents
```

By default, constructing a `QdrantVectorStore` with `location=":memory:"` keeps
everything in memory — gone when the process exits, which is why every topic so far
rebuilds its store on each run. Passing `path="./qdrant_db"` instead writes the index to
disk so a later process can reopen it without re-embedding anything (re-embedding costs
API calls and time).

## Minimal code

`code.py` splits a document into chunks (Topic 03's splitter), embeds them into a
**persisted** Qdrant store on disk, runs a similarity search, then reopens the *same*
on-disk store in a fresh `QdrantVectorStore(...)` call (no `.from_documents`, no
re-embedding) and proves the data survived — the actual behavior that makes persistence
worth doing.

## Production notes

Pick one embedding model per vector store and never mix (Phase 0 Topic 05's warning) —
if you switch models, every existing vector is now incomparable to new queries and the
whole store needs re-embedding from scratch. Store the model name in your own
config/metadata so a future you can tell which model a given store was built with.

## Debugging

- Reopening a persisted store returns 0 results → check `path` (and `collection_name`)
  point to the exact same values used when the store was created — a relative path
  resolved from a different working directory silently points at an empty/new directory.
- Query results look random/irrelevant after reopening → almost always an embedding
  model mismatch between the write and the read (Phase 2 Topic 06's debugging note).

## Mini challenge

Run `code.py` twice in a row without deleting the `qdrant_db` folder it creates, and
confirm the second run's "reopen" step finds the data instantly with zero embedding
calls — then delete the folder and re-run to see the from-scratch cost.
