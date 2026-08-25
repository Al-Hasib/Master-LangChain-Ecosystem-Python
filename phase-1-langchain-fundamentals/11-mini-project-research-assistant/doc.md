# 11 — Mini Project: AI Research Assistant v1

## Problem

Bring together everything from Phase 1 into one working agent, closing out the phase
the same way Phase 0 closed with its mini project — and giving Phase 2+ a real, running
baseline to keep extending.

## Concept

```text
User
  ↓
LangChain Agent  (Topic 06: create_agent)
  ↓
LLM              (Topic 02: init_chat_model)
  ↓
Tools            (Topic 05: @tool)
 ├── Calculator
 ├── Web Search
 └── Date/Time
```

Design decisions worth calling out on camera:
- **Calculator** is implemented as real Python arithmetic (not another LLM call) —
  tools should do deterministic work the model is bad at, not work it's already good at.
- **Web search** uses DuckDuckGo (no API key required) so the project runs for every
  viewer out of the box; swapping in Tavily/another provider is a one-tool change.
- **Date/time** is included specifically because models don't reliably know "today's
  date" — a trivial tool fixes a surprisingly common failure mode.
- The system prompt explicitly tells the agent when each tool applies, applying Topic
  05's lesson about docstrings/descriptions driving tool selection.

This project becomes **"v1"** deliberately — Phase 3 gives it a real knowledge base
(RAG), Phase 5 makes it decide *when* to retrieve, Phase 6 rebuilds it as an explicit
LangGraph graph, and Phase 9 makes it observable. Same application, growing phase by
phase, per this repo's "one evolving project" narrative.

## Minimal code

`code.py` wires three tools into one `create_agent` agent and runs it against a few
questions that each require a different tool (or none), printing the full message trace
per question so every tool decision is visible.

## Production notes

Nothing here is production-ready yet — no memory across sessions, no error boundaries
around tool failures, no observability. That's intentional: Phase 1 ends with the
simplest correct version; hardening it is what later phases are for.

## Debugging

If the agent answers a date/math question without using its tool, check the system
prompt is explicit that tools should be preferred over the model's own knowledge for
those categories — models will "wing it" on math and dates if not told otherwise.

## Mini challenge

Add a fourth tool (e.g. a currency converter using fixed exchange rates) and ask a
question that chains three tools in one request (search → calculate → format with a
date).
