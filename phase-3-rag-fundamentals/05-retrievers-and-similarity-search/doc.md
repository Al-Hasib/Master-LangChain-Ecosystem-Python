# 05 — Retrievers & Similarity Search

## Problem

Every topic so far called `vector_store.similarity_search(...)` directly. That works,
but it couples your RAG code to a specific *vector store* object — not to the standard
`Retriever` interface the rest of LangChain (LCEL chains, and later, agents-as-tools in
Phase 5) is built to compose with. Phase 2 Topic 06 already flagged this; this topic
puts it to use.

## Concept

`.as_retriever()` wraps a vector store in a `Retriever` — a `Runnable` (Phase 1 Topic 03
territory) with one method that matters here: `.invoke(query)`.

```python
retriever = vector_store.as_retriever(search_kwargs={"k": 3})
documents = retriever.invoke("How long do refunds take?")   # list[Document], same as similarity_search
```

`search_kwargs={"k": n}` is the retriever equivalent of `similarity_search(query, k=n)`
— fixed top-k results, always. The second mode, `search_type="similarity_score_threshold"`,
inverts that: instead of a fixed count, it returns *every* result whose relevance score
clears a threshold, which can be 0 results or many:

```python
retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.75},
)
```

```text
top-k mode:                              score-threshold mode:
query -> search -> ALWAYS top 3           query -> search -> only results scoring >= 0.75
         (even if #3 is barely relevant)             (could be 0, could be 10)
```

Top-k is predictable (always feeds the LLM the same amount of context) but can hand over
weak matches just to fill the quota. Score-threshold guarantees relevance but can return
nothing — your downstream code (Topic 07's prompt) has to handle an empty context
gracefully either way.

## Minimal code

`code.py` builds one Chroma store, wraps it as a retriever two ways — default top-k and
score-threshold — and runs the *same* query through both `.invoke(...)` calls, printing
result counts side by side so the difference in behavior is concrete, not theoretical.

## Production notes

Prefer `.as_retriever()` over calling `similarity_search` directly once a RAG chain is
being wired together (Topic 07) — a retriever composes into LCEL pipelines the same way
`prompt | model` did in Phase 1 Topic 03, while a raw vector store's methods don't.

## Debugging

- Score-threshold retriever returns an empty list with no error → this is expected
  behavior, not a bug — always check for empty results and handle that case in your
  prompt/response logic (Topic 01's "say you don't know" pattern).
- Top-k retriever returns `k` results that all look weakly relevant → the corpus may
  genuinely not contain a strong match; score-threshold mode would have surfaced that as
  an empty list instead of hiding it behind a fixed count.

## Mini challenge

Sweep `score_threshold` from `0.9` down to `0.3` in increments and print the result
count at each value — find the threshold where your demo corpus's relevant document
first appears, and note how sensitive that number is to your specific embedding model
and corpus.
