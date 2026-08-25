# 05 — Parent-Document & Multi-Vector Retrieval

## Problem

Chunk size is a tug-of-war. **Small chunks** search well — a tight, focused chunk
matches a specific query precisely, which is why Phase 3's splitter defaults skew small.
But a small chunk handed to the LLM in isolation often lacks the surrounding context
needed to answer well (a sentence explaining "the rate limit" with no sentence nearby
saying *which* plan it applies to). **Large chunks** give the LLM context, but dilute
retrieval precision — this is Topic 01's "irrelevant chunk" failure mode from the other
direction: too much unrelated text riding along with the relevant sentence.

## Concept

**ParentDocumentRetriever** resolves the tug-of-war by decoupling *what gets searched*
from *what gets returned*: split into small child chunks for indexing/search precision,
but store and return the larger parent chunk (or whole original document) that child
came from, once a match is found.

```text
indexing:
  original doc -> parent_splitter (large chunks, or none = whole doc) -> parent chunks
                                                                            │
                                              each parent -> child_splitter (small chunks)
                                                                            │
                                                          child chunks -> embedded -> vector store
                                                          (vector store only ever holds children)

query time:
  query -> vector search over CHILD embeddings -> best-matching child
                                                        │
                                     look up child's parent id in the docstore
                                                        │
                                     return the FULL PARENT chunk to the LLM
```

```python
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,       # indexes only the small child chunks
    docstore=InMemoryStore(),      # holds the full parent chunks, keyed by id
    child_splitter=RecursiveCharacterTextSplitter(chunk_size=200),
    parent_splitter=RecursiveCharacterTextSplitter(chunk_size=800),  # omit to use whole docs as parents
)
retriever.add_documents(documents)
docs = retriever.invoke(query)  # returns PARENT chunks, even though search matched a CHILD
```

**Multi-vector retrieval** is the general pattern this specializes: index *any* derived
representation of a document (small chunks, an LLM-written summary, hypothetical
questions the doc could answer — even a HyDE-style artifact from Topic 02) pointing back
to the same stored parent via an `id_key`, so the thing you search over and the thing
you generate from don't have to be the same text.
`langchain_classic.retrievers.multi_vector.MultiVectorRetriever` is the base class —
`ParentDocumentRetriever` is `MultiVectorRetriever` pre-wired for the "small splits point
back to their parent" case specifically.

## Minimal code

`code.py` builds one long Nimbus "deployment runbook" document, indexes it with
`ParentDocumentRetriever` (small child chunks for search, whole-document parents for
generation), runs a query that only matches a small fragment of the runbook, and prints
both the matched child chunk and the full parent content actually returned — showing the
gap between what was searched and what was returned.

## Production notes

Project B (Documentation RAG) is built on this pattern: search precision over individual
sections, full-page/section context for generation, "freshness-aware" in that
re-indexing an updated page only requires re-splitting and re-embedding its children —
the parent store update is a simple upsert. `InMemoryStore` (used here for a standalone
demo) is memory-only and disappears on restart; production needs a persistent docstore
(Redis, a SQL table, or any key-value store implementing the same interface).

## Debugging

- Retriever returns child-sized chunks, not full parents → check `parent_splitter` isn't
  accidentally the same size as `child_splitter`, and that `add_documents` was called on
  the retriever (not on the vector store directly, which would skip the parent/child
  bookkeeping).
- Parent lookups return `None` → the `id_key` used when adding documents doesn't match
  what the vector store's child metadata stores; don't set child ids manually unless
  you're also managing the docstore keys yourself.

## Mini challenge

Swap `parent_splitter` for `None` so parents are the entire original document rather
than 800-character sections, and compare how much extra (possibly irrelevant) text now
comes back per query — the same "big chunk dilutes precision" trade-off shows up again
one level higher.
