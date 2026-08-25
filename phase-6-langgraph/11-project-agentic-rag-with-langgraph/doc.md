# 11 — Project: Agentic RAG with LangGraph

## Problem

Phase 5's agentic RAG (retrieve → grade → maybe rewrite and retry → generate) runs that
whole decision process *inside* one agent loop — you can see the final answer, but the
grading and rewrite decisions happen inside the model's tool-calling behavior, not as
steps you can point at individually. As a graph, every one of those decisions is its own
node you can inspect, log, or replay (Topic 07).

## Concept

```text
START ─► retrieve ─► grade_documents ──relevant?──yes──► generate ─► END
              ▲                            │
              │                            no (and under the rewrite limit)
              └──────── rewrite_query ◄─────┘
```

- `retrieve` — runs a similarity search against a small in-code Chroma knowledge base
  (Phase 3 Topic 05's retriever pattern) and stores the returned chunks in state.
- `grade_documents` — one focused LLM call: "do these chunks actually answer the
  question?" → `"yes"` / `"no"`. This is the piece that's invisible inside a plain agent
  loop — here it's a node with its own input/output you can log.
- conditional edge — relevant → straight to `generate`; not relevant (and still under a
  rewrite budget) → `rewrite_query`, which loops back to `retrieve` with a reformulated
  question. A rewrite-count cap in state prevents an infinite loop if retrieval keeps
  coming up empty.
- `generate` — the final LLM call, grounded only in the (graded-relevant) retrieved
  chunks.

## Minimal code

`code.py` builds a five-document in-code knowledge base about a fictional product with
`Chroma.from_documents` + `OpenAIEmbeddings`, wires the graph above, and runs two
questions: one that's answerable directly from the knowledge base (grades relevant on the
first pass) and one deliberately vague question that's expected to trigger at least one
`rewrite_query` loop before generating.

## Production notes

Log every `grade_documents` decision in a real system — a grader that's consistently too
lenient (marking irrelevant chunks "relevant") silently degrades answer quality without
ever raising an error. The rewrite-count cap is not optional: without it, a knowledge
base that genuinely doesn't contain the answer produces an infinite retrieve/rewrite
loop instead of a "couldn't find an answer" response.

## Debugging

- Same question rewritten identically every rewrite loop → the rewrite prompt isn't
  being given the *previous* question/attempt as context, so the model has no signal to
  change anything.
- `generate` produces a confident-sounding answer that isn't in the knowledge base at all
  → `grade_documents` is marking irrelevant chunks relevant; tighten its prompt to
  require an explicit connection between the chunk and the question.

## Mini challenge

Add a `max_rewrites` field to state (instead of a hardcoded cap in the router function)
and confirm the graph falls through to `generate` with whatever documents it has once the
budget is exhausted, rather than looping forever.
