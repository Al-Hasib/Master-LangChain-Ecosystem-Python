# 04 — Document Loaders — Common Formats

## Problem

Phase 0 built `Document`-like data by hand from a Python list of strings. Real content
lives in PDFs, web pages, spreadsheets, JSON exports, Markdown files, and databases —
each with a completely different file format but needing to end up as the *same* thing:
a list of `Document` objects with `page_content` + `metadata`.

## Concept

Every LangChain document loader implements the same tiny interface:

```python
loader = SomeLoader(...)
documents = loader.load()   # -> list[Document], each with .page_content and .metadata
```

That uniformity is the entire point — once data is loaded, everything downstream (text
splitting, embedding, vector storage — Phase 3) doesn't care whether it originally came
from a PDF or a CSV row.

| Format | Loader | Notes |
|---|---|---|
| PDF | `PyPDFLoader` | one `Document` per page; `metadata["page"]` set automatically |
| Web page | `WebBaseLoader` | fetches + strips HTML via BeautifulSoup |
| CSV | `CSVLoader` | one `Document` per row by default |
| JSON | *(build manually)* | `JSONLoader` needs the native `jq` library, which is painful to install on Windows — for irregular JSON, mapping records to `Document`s yourself is often less friction and just as correct |
| Markdown | `TextLoader` (simple) / `UnstructuredMarkdownLoader` (structure-aware, heavier dependency) | this course uses `TextLoader` to keep the dependency list light |
| SQL / database rows | *(build manually, same pattern as JSON)* | each row becomes one `Document`, columns become `metadata` |

The lesson isn't "memorize every loader" — it's: **whatever the source, the exit shape
is `list[Document]`.** For sources with no dedicated loader (or where the dedicated
loader adds a dependency you don't want), writing a 5-line function that wraps your data
in `Document(page_content=..., metadata=...)` is completely idiomatic — that's literally
what a document loader is.

## Minimal code

`code.py` loads the *same conceptual content* from five different formats — a
generated-on-the-fly PDF, CSV, Markdown file, a JSON list, and SQLite rows — into
`Document` objects, printing each source's document count and one example so the shared
shape is obvious. A web-page load is included and gracefully skipped if there's no
network access.

## Production notes

Always populate `metadata["source"]` (file path, URL, table name) at load time —
Phase 3's citation feature and Phase 4's filtering both depend on knowing where a chunk
came from *before* it gets split and mixed with everything else.

## Debugging

- `CSVLoader`/`PyPDFLoader` raising on a real file → check the file path is correct
  relative to where you run the script from, not relative to the loader file.
- Empty `page_content` from a scanned/image-only PDF → `PyPDFLoader` extracts text
  layers only; scanned documents need OCR (out of scope for this course).

## Mini challenge

Point `PyPDFLoader` at a real multi-page PDF you have locally and print
`metadata["page"]` for each resulting `Document` to see the one-`Document`-per-page
behavior directly.
