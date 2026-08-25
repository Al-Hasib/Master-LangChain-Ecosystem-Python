# 06 — Metadata Filtering

## Problem

Similarity alone can't distinguish *source*, only *meaning*. Two different products'
documentation can both mention "warranty" in semantically similar ways — a pure
similarity search can't tell you want only the TrailBlazer backpack's warranty, not the
SummitPro tent's. Topic 02 established `metadata` as a first-class field precisely so
you can narrow search by structured facts (source, category, date) *before or alongside*
semantic ranking.

## Concept

Chroma (via `langchain_chroma`) accepts a `filter` argument on `similarity_search`, and
the equivalent `search_kwargs={"filter": ...}` on a retriever (Topic 05):

```python
vector_store.similarity_search(query, k=3, filter={"category": "product"})

retriever = vector_store.as_retriever(
    search_kwargs={"k": 3, "filter": {"category": "product"}}
)
```

The filter dict has two forms. A plain `{"key": "value"}` is shorthand for exact-match
equality. For multiple conditions or operators other than equality, use Chroma's
explicit operator syntax:

```python
{"$and": [{"category": {"$eq": "policy"}}, {"topic": {"$eq": "returns"}}]}
```

Supported operators include `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, combined with
`$and` / `$or`. The filter is applied *as part of* the nearest-neighbor search, not as a
separate pass afterward — so it narrows the search space instead of just discarding
results after the fact.

```text
query embedding
        │
        ▼
vector search  ──restricted to── metadata WHERE category = "product"
        │
        ▼
top-k results, all guaranteed to match the filter AND rank by similarity
```

## Minimal code

`code.py` builds a small two-product corpus where both products' chunks mention
"warranty" (deliberately overlapping vocabulary), tagged with `metadata={"product": "..."}`.
It runs the same query once unfiltered (both products' chunks are candidates) and once
with `filter={"product": "TrailBlazer 40L"}`, printing both result sets so the narrowing
effect is visible.

## Production notes

Populate the metadata keys you know you'll filter on (source, category, tenant/customer
ID, date) at ingest time (Topic 02's production note) — you cannot filter on a field
that was never recorded. In multi-tenant RAG systems, a metadata filter on tenant ID is
often a hard *security* boundary, not just a relevance nicety — get it right.

## Debugging

- Filter returns zero results even though matching documents exist → metadata values are
  matched exactly and are case-sensitive; `"TrailBlazer 40L"` won't match `"trailblazer 40l"`.
- `$and`/`$or` filter raises an error → each condition must be its own single-key dict
  inside the list — `{"$and": [{"a": {"$eq": 1}}, {"b": {"$eq": 2}}]}`, not a single
  multi-key dict.

## Mini challenge

Add a third product and write a `$or` filter that matches two of the three products at
once, confirming the unfiltered document count minus the matched count equals the
excluded product's chunk count.
