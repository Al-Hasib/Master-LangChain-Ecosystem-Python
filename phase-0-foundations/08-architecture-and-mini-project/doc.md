# 08 — Architecture of a Modern AI App & Mini Project

## Problem

Viewers have seven separate concepts now (LLM/chat/agent, tokens, messages, structured
output/tools, embeddings, vector DBs, RAG/agent/workflow). This topic assembles them
into one picture and one small working program, so Phase 1 has something concrete to
"replace with LangChain" — making every subsequent abstraction land as "oh, that's
doing what I just wrote by hand."

## Concept

A modern AI application, stripped to its essential layers:

```text
                         USER
                          │
                          ▼
                    Application code           <- your code: routes input, calls the model
                          │
              ┌───────────┼────────────┐
              ▼           ▼            ▼
          Chat Model     Tools     Vector Store   <- Topics 01-06
              │           │            │
              └───────────┴────────────┘
                          │
                          ▼
                  Structured response            <- Topic 04
```

Every framework in this course (LangChain, LangGraph, Deep Agents) is a set of
abstractions over exactly this picture: a standard interface for the model, a standard
interface for tools, a standard interface for vector stores, and standard control-flow
patterns (chain / agent loop / graph) for wiring them together. Nothing new is being
invented — repetition is being removed.

## Minimal code — Mini Project: Tiny LLM App (no framework)

`code.py` is a small CLI: it takes a question, decides (via one tool-calling round trip)
whether to search a tiny local knowledge base, and prints a structured JSON answer with
a `source` field. It reuses ideas from every prior topic in this phase:

- Chat model call with a system message (Topics 01, 03)
- Tool calling for the retrieval decision (Topic 04)
- A Chroma-backed knowledge base (Topic 06)
- Structured JSON output for the final answer (Topic 04)

This is deliberately close to what Phase 1's `create_agent` will do in ~10 lines instead
of ~80 — the goal is that the reduction feels earned, not magic.

## Production notes

Real applications add: persistent conversation state, error handling/retries per call,
observability (Phase 9), and usually a web API in front (Phase 10) — but the core shape
above doesn't change.

## Debugging

If this script's behavior seems confusing, that confusion *is the motivation* for Phase
1 — note down specifically what felt manual/repetitive/fragile, and check whether
LangChain's abstractions address it.

## Mini challenge

Extend the knowledge base with 2 more facts and add a second tool (e.g. `get_time`) so
the app has to choose between two possible tools, not just decide yes/no on one.
