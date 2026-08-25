# 07 — What is RAG? & RAG vs Agent vs Workflow

## Problem

By now viewers know: chat models, tool calling, embeddings, vector search. This topic
assembles those parts into the three application *shapes* the rest of the course keeps
returning to, and gives viewers a way to decide which shape a given problem needs.

## Concept

**RAG (Retrieval-Augmented Generation):** retrieve relevant documents (via the vector
search from Topic 06), then generate an answer using them as context. Fixes two LLM
weaknesses at once: knowledge cutoff and hallucination on facts outside training data.

```text
Question -> embed -> vector search -> top-k documents -> [documents + question] -> LLM -> Answer
```

**Workflow (fixed pipeline):** a predetermined sequence of steps, each possibly an LLM
call, tool call, or plain code — the *order* is fixed by you, not decided by the model.
Basic RAG above is a workflow: retrieve always happens, then generate always happens.

**Agent:** the model itself decides, per turn, what happens next — which tool to call
(if any), whether to retrieve, when it's done. Control flow lives in the loop, not in
your code's explicit sequence.

```text
Workflow:  step1 -> step2 -> step3                          (you decide the order)
Agent:     loop { model decides: answer | call_tool -> observe -> repeat }  (model decides)
```

These aren't mutually exclusive — **Agentic RAG** (Phase 5) is an agent that has
retrieval available as one of its tools, deciding *whether and when* to retrieve rather
than always retrieving. Most real systems are a mix: a workflow skeleton with an agent
step somewhere inside it, or an agent with workflow-like tools.

**Decision framework:**
| Need | Reach for |
|---|---|
| Answer questions from a fixed knowledge base, predictable steps | RAG (workflow) |
| Multiple knowledge sources, model should decide which to consult | Agentic RAG |
| Take actions (send email, query DB, call APIs), order not fixed | Agent |
| Strict, auditable, repeatable multi-step process | Workflow (LangGraph, Phase 6) |

## Minimal code

`code.py` implements the same question two ways: as a fixed RAG workflow (always
retrieve, then generate) and as a one-step agent decision (let the model decide whether
retrieval is even needed for a given question) — using the Chroma collection pattern
from Topic 06.

## Production notes

Default to the *simplest shape that solves the problem*. Fixed workflows are easier to
test, debug, and reason about than agents — only reach for agent autonomy when the task
genuinely has variable steps the model needs to decide.

## Debugging

- RAG "hallucinates" despite having retrieved context → the model is ignoring/not
  grounding in the retrieved context; needs stronger prompting ("answer only using the
  provided context") — full treatment in Phase 3–4.
- Agent takes too many/unpredictable steps for a task that's actually always the same
  sequence → you probably want a workflow, not an agent.

## Mini challenge

Take a question that doesn't need the knowledge base at all (e.g. "what's 12 * 7?") and
run it through both the fixed-RAG version and the agent-decision version — observe the
fixed version wastefully retrieves anyway, while the agent skips retrieval.
