# 08 — Mini Project: Multi-Source Connector

## Problem

Close out Phase 2 by proving the whole point of the phase: heterogeneous sources
(different loaders, different original formats) can be normalized into one consistent
pipeline and one vector store, because every step in the chain agreed on the same
shape — `Document` in, `Document` out.

## Concept

```text
CSV file  ──┐
Markdown  ──┼─► loader.load() ─► list[Document] ─► normalize metadata ─► Chroma
GitHub API──┘         (Topic 04/05)      (this project)      (Topic 06)
```

The one new idea this project adds on top of Topics 04–06: **normalizing metadata
across sources before they land in the same vector store.** A `CSVLoader` document and a
hand-built GitHub-adapter document won't have the same metadata keys by default — this
project defines one consistent schema (`source_type`, `source_name`, `origin`) applied
to every document regardless of where it came from, so a later filtered search (Phase
3–4) can reliably ask "only search my `source_type='handbook'` documents."

## Minimal code

`code.py` pulls from three sources — a local CSV (policies), a local Markdown file
(handbook), and the GitHub README adapter from Topic 05 — normalizes each source's
documents to the shared metadata schema, loads everything into one Chroma collection,
and runs a similarity search that could only be answered by combining knowledge from
more than one source's documents.

## Production notes

Normalize metadata **at ingestion time**, not at query time — trying to reconcile
inconsistent metadata schemas after documents are already mixed in a vector store is
much harder than enforcing a schema on the way in.

## Debugging

If a filtered search unexpectedly returns nothing, print `document.metadata` for a
sample of what's in the store first — a silent metadata-key mismatch (`"source"` vs.
`"source_name"`) is the most common cause.

## Mini challenge

Add a fourth source (reuse Topic 04's JSON FAQ example) into the same normalized
pipeline, and confirm a similarity search can surface a result from all four original
sources for a sufficiently broad query.
