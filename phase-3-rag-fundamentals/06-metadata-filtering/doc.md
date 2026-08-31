# 06 — Metadata Filtering

## Problem

Similarity alone can't distinguish *source*, only *meaning*. Two different products'
documentation can both mention "warranty" in semantically similar ways — a pure
similarity search can't tell you want only the TrailBlazer backpack's warranty, not the
SummitPro tent's. Topic 02 established `metadata` as a first-class field precisely so
you can narrow search by structured facts (source, category, date) *before or alongside*
semantic ranking.

## Concept

`QdrantVectorStore` (via `langchain_qdrant`) accepts a `filter` argument on
`similarity_search`, and the equivalent `search_kwargs={"filter": ...}` on a retriever
(Topic 05). Unlike a plain dict, the filter is a `qdrant_client.models.Filter` object —
Qdrant's native filter syntax, passed straight through:

```python
from qdrant_client import models

category_filter = models.Filter(
    must=[models.FieldCondition(key="metadata.category", match=models.MatchValue(value="product"))]
)

vector_store.similarity_search(query, k=3, filter=category_filter)

retriever = vector_store.as_retriever(
    search_kwargs={"k": 3, "filter": category_filter}
)
```

Note the `"metadata."` prefix on the key — `QdrantVectorStore` nests each LangChain
`Document`'s `metadata` dict under a `metadata` payload key on the stored point, so a
filter on `category` targets `metadata.category`, not a bare top-level `category` field.

A single condition is a `Filter` with one `FieldCondition` in `must=[...]`. For multiple
AND conditions, add more entries to the same `must` list; for OR, use `should=[...]`
instead:

```python
models.Filter(
    must=[
        models.FieldCondition(key="metadata.category", match=models.MatchValue(value="policy")),
        models.FieldCondition(key="metadata.topic", match=models.MatchValue(value="returns")),
    ]
)
```

`FieldCondition` also supports range conditions (`models.Range(gt=..., gte=..., lt=...,
lte=...)`) alongside `match` for equality. The filter is applied *as part of* the
nearest-neighbor search, not as a separate pass afterward — so it narrows the search
space instead of just discarding results after the fact.

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
with a `models.Filter` matching `metadata.product == "TrailBlazer 40L"`, printing both
result sets so the narrowing effect is visible.

## Production notes

Populate the metadata keys you know you'll filter on (source, category, tenant/customer
ID, date) at ingest time (Topic 02's production note) — you cannot filter on a field
that was never recorded. In multi-tenant RAG systems, a metadata filter on tenant ID is
often a hard *security* boundary, not just a relevance nicety — get it right.

## Debugging

- Filter returns zero results even though matching documents exist → metadata values are
  matched exactly and are case-sensitive; `"TrailBlazer 40L"` won't match `"trailblazer 40l"`.
  Also double-check the key has the `metadata.` prefix — `key="product"` silently
  matches nothing because the payload field is actually `metadata.product`.
- `Filter` raises a validation error → each condition must be its own `FieldCondition`
  inside the `must=[...]` (or `should=[...]`) list, not a raw dict — construct it with
  `qdrant_client.models`, not hand-rolled JSON.

## Mini challenge

Add a third product and write a filter using `should=[...]` (Qdrant's OR) that matches
two of the three products at once, confirming the unfiltered document count minus the
matched count equals the excluded product's chunk count.
