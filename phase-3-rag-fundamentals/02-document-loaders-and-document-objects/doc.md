# 02 — Document Loaders & Document Objects

## Problem

Topic 01 built `Document` objects by hand from a Python list of strings. Real knowledge
lives in PDFs, spreadsheets, web pages, and databases — Phase 2 Topic 04 already showed
how to turn all of those into `Document`s. This topic doesn't re-teach loaders; it
zooms in on the `Document` object itself, because that's the one shape every remaining
Phase 3 topic (splitting, embedding, retrieving, filtering, citing) operates on.

## Concept

A `Document` is deliberately boring: two fields.

```python
class Document:
    page_content: str   # the actual text
    metadata: dict       # everything ABOUT the text: source, page number, etc.
```

`page_content` is what gets embedded (Topic 04) and shown to the LLM (Topic 07).
`metadata` never gets embedded, but it survives splitting (Topic 03) and rides along
into the vector store — it's what makes citations ("page 4 of handbook.pdf," Topic 07)
and metadata filtering (Topic 06) possible at all.

```text
raw file (PDF / CSV / ...)
        │  loader.load()          <- Phase 2 Topic 04
        ▼
[ Document(page_content="...", metadata={"source": "handbook.pdf", "page": 3}), ... ]
        │
        ▼
  every downstream Phase 3 step only ever touches page_content + metadata
  (splitter, embedder, vector store, retriever, citation logic)
```

Because every loader returns `list[Document]` regardless of source format (Phase 2
Topic 04's core lesson), the rest of this phase never needs to know or care whether a
chunk originally came from a PDF, a CSV row, or a hand-built `Document` like Topic 01's.

## Minimal code

`code.py` loads a generated-on-the-fly PDF (via `PyPDFLoader`, same trick as Phase 2
Topic 04 — blank pages, since this is about loader/Document mechanics, not text
extraction) and a generated CSV (via `CSVLoader`, real text this time), then prints
`page_content` and `metadata` for each so the shared shape is obvious across two
completely different source formats. It also builds one `Document` by hand to show the
loader isn't doing anything magical — it's just automating exactly that construction.

## Production notes

Always populate `metadata["source"]` at load time (Phase 2 Topic 04's production note) —
by the time a chunk is sitting in a vector store next to a thousand others, there's no
way to recover where it came from unless the loader recorded it up front.

## Debugging

- `AttributeError` on `.page_content` → you're holding a raw string or a loader's
  intermediate object, not a `Document` — check what the loader actually returned.
- Metadata missing a field you expected → not every loader populates the same metadata
  keys (`PyPDFLoader` adds `"page"`; a hand-built `Document` has whatever you gave it) —
  never assume a key exists without checking, especially across mixed sources.

## Mini challenge

Load the generated CSV, then manually add a `metadata["ingested_at"]` timestamp to
every resulting `Document` — this is the same pattern production ingestion pipelines use
to track data freshness.
