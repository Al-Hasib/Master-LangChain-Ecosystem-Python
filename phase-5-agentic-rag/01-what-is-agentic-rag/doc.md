# 01 — What is Agentic RAG?

## Problem

Phase 3 and Phase 4 built increasingly capable retrieval pipelines, but every one of
them shares the same property: retrieval **always** happens. The pipeline never asks
"do I even need to search the knowledge base for this?" — it retrieves on every call,
even for "what's 12 times 7?" That's wasted latency and cost on questions the model
could answer directly, and it's exactly the line Phase 0 Topic 07 drew between
**workflow** (fixed order, you decide) and **agent** (model decides, per turn). This
phase puts retrieval on the agent side of that line.

## Concept

Same knowledge base, two shapes for answering a question:

**Fixed-pipeline RAG (Phase 3–4):** retrieve, then generate — no matter what the
question is.

```text
Question -> retriever.invoke()  [ALWAYS]  -> [context + question] -> LLM -> Answer
```

**Agent-directed retrieval (this phase):** retrieval is just one tool; the agent (the
`create_agent` loop from Phase 1 Topic 06) decides, per question, whether to call it.

```text
Question -> Agent loop { model decides: answer directly | call search_tool -> observe -> repeat } -> Answer
```

This is the exact RAG-vs-agent distinction Phase 0 Topic 07 drew, now applied
specifically to retrieval. Topic 07's `agent_decision_step` hand-rolled *one* manual
tool-call round trip with the raw OpenAI SDK. This phase replaces that by hand-rolled
loop with the real `create_agent` loop, which can call the retrieval tool zero, one, or
several times before producing a final answer — the same mechanic Phase 1 Topic 06
introduced, now aimed at retrieval specifically.

## Minimal code

`code.py` builds one small Qdrant-backed knowledge base (Aurora Cloud Analytics'
policies) and answers two questions two ways: `fixed_rag_workflow` (always retrieves)
and an agent built with `create_agent` given a retrieval tool (decides whether to
retrieve). One question needs the knowledge base; one ("what's 12 times 7?") doesn't —
watch the fixed pipeline retrieve anyway while the agent skips it entirely.

## Production notes

Agent-directed retrieval costs an extra model round trip (deciding *whether* to call the
tool) compared to always retrieving. For a system where retrieval is nearly always
needed, fixed RAG is simpler, cheaper, and easier to test — don't reach for an agent
just because it's more flexible. Agent-directed retrieval earns its keep once a system
has multiple knowledge sources (Topic 03) or a real fraction of questions that need no
retrieval at all.

## Debugging

- Agent retrieves for every question anyway → the tool's description probably doesn't
  say when *not* to use it; the model defaults to "when in doubt, call it."
- Agent never retrieves, even for knowledge-base questions → the tool description or
  system prompt is underselling what the tool covers; be explicit about the domain.

## Mini challenge

Add a third, borderline question (e.g. "What comes with the premium plan?" — plausibly
either general knowledge or a KB lookup) and see which way the agent decides. Tighten
the tool's description until it decides correctly and consistently.
