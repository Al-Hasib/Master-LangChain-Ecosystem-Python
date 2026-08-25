# 08 — RAG Evaluation Basics

## Problem

Topic 07 built a full pipeline and just *assumed* retrieval was working because the
answers looked reasonable. "Looks reasonable" isn't measurement. Before Phase 9
introduces LangSmith's proper dataset/eval tooling, a small hand-labeled query set gives
an immediate, dependency-free way to check retrieval quality with numbers instead of
vibes.

## Concept

**Precision@k**: of the top-k documents a retriever returns for a query, what fraction
are actually relevant, according to a human-labeled ground truth? A simple, honest proxy
for "is retrieval finding the right stuff."

```text
precision@k = (# retrieved docs that are actually relevant) / k
```

The manual eval loop this topic uses:

```text
labeled set: [(query, {expected relevant doc ids}), ...]
        │
        ▼  for each (query, expected) pair:
        ▼    retrieved = retriever.invoke(query)
        ▼    hits = retrieved docs whose id is in `expected`
        ▼    precision@k = len(hits) / k
        ▼
        ▼  average precision@k across all queries -> overall retrieval score
```

This requires you to hand-label a small set of queries with which document(s) *should*
come back — tedious, but that tedium is the entire point: it forces you to define
"correct" concretely instead of eyeballing final answers. This is retrieval evaluation
specifically; it says nothing about whether the LLM's generated *answer* used the
retrieved context well (that's answer-relevance evaluation, which needs an LLM-as-judge
approach — covered properly with LangSmith in Phase 9).

## Minimal code

`code.py` reuses the two-product corpus style from Topic 06, tags each document with a
stable id, hand-labels 4 queries with their expected relevant doc id(s), runs each
query through a `k=2` retriever, computes precision@k per query, and prints a summary
table plus the overall average.

## Production notes

A golden set like this belongs in your test suite even after adopting LangSmith
(Phase 9) — it's fast, has zero external dependencies, and catches obvious retrieval
regressions (e.g., someone changes `chunk_size` and precision quietly drops) in CI
before a human ever notices. LangSmith adds versioned datasets, experiment tracking, and
LLM-as-judge answer-quality scoring on top of the same underlying idea.

## Debugging

- Precision@k is perfect (1.0) on your hand-labeled set but retrieval "feels wrong" in
  real use → toy labeled sets are almost always too small/easy; add harder, more
  ambiguous queries before trusting the number.
- Precision@k is low despite obviously-relevant documents existing in the corpus →
  check `k` is large enough to include them, and that chunking (Topic 03) isn't
  fragmenting the relevant fact across a chunk boundary the retriever ranks lower.

## Mini challenge

Add one deliberately ambiguous query (phrased so it could plausibly match either
product) to the labeled set, and watch precision@k drop — this is the first real signal
that your retrieval setup needs improvement, which is exactly what Phase 4 addresses.
