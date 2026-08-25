# 03 — Text Splitting & Chunking Strategies

## Problem

A loaded `Document` (Topic 02) is often way bigger than one coherent "fact" — a whole
PDF page, a whole handbook section. Embedding that entire blob as a single vector
(Topic 04) blurs multiple ideas into one point in vector space, so a query about one of
those ideas retrieves a chunk that's only partly relevant, diluted by everything else
crammed in alongside it. Splitting **before** embedding fixes this.

## Concept

`RecursiveCharacterTextSplitter` (from the `langchain_text_splitters` package) is the
default splitter: it tries to split on paragraph breaks first, then sentences, then
words, then characters — recursively falling back until pieces fit under `chunk_size`.
`chunk_overlap` repeats a few characters between consecutive chunks so a fact sitting
right at a chunk boundary doesn't get cut in half with no surrounding context on either
side.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)   # list[Document] in -> list[Document] out
```

`split_documents` preserves each input `Document`'s `metadata` onto every chunk it
produces (Topic 02's metadata survives splitting) — this is exactly what makes
page-level citations (Topic 07) possible after a page gets split into three chunks.

```text
one Document (2000 chars, covers returns + shipping + refunds)
        │
        ▼  RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        ▼
[chunk1(0-500), chunk2(450-950), chunk3(900-1400), chunk4(1350-1850), ...]
        overlapping windows, metadata copied onto each chunk
```

**Chunk size is a tradeoff, not a "bigger is safer" setting:**
- Too large → multiple unrelated facts get embedded into one vector; a query about one
  fact retrieves a chunk polluted with the others, hurting relevance.
- Too small → a chunk loses the surrounding context a sentence needs to make sense on
  its own (a pronoun with no antecedent, a fact with no subject).

## Minimal code

`code.py` builds one longer synthetic document mixing five unrelated policy facts into
continuous prose, then splits it two ways: `chunk_size=800, overlap=0` (coarse — most
facts end up bundled together) vs. `chunk_size=150, overlap=20` (fine-grained — closer
to one fact per chunk). Both versions get embedded into separate Chroma stores and
queried with the same question, printing the top match from each so you can see the
coarse version's top chunk drag in unrelated text while the fine version's top chunk is
tightly on-topic.

## Production notes

There's no universal "correct" chunk size — it depends on how atomic your source facts
are and which embedding model you're using. Start around 500–1000 characters with
10–20% overlap and tune from retrieval quality (Topic 08), not guesswork. Phase 4 covers
smarter strategies (semantic chunking, structure-aware splitting) once this baseline
stops being good enough.

## Debugging

- Retrieved chunk cuts off mid-sentence with no context → increase `chunk_overlap`.
- Retrieval feels "unfocused," pulling back plausible-but-wrong chunks → `chunk_size` is
  probably too large for how dense your source facts are; shrink it.
- A chunk reads as gibberish/fragmentary on its own → `chunk_size` is too small,
  fragmenting a single sentence or thought across chunk boundaries.

## Mini challenge

Set `chunk_size=40` (deliberately too small) and print the resulting chunks — observe
how many mid-sentence, context-free fragments come out, and how that would hurt an LLM
trying to answer from just one of them.
