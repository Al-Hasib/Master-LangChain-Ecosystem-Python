# 01 — What is LangChain? & Architecture

## Problem

Phase 0's mini project (~140 lines) hand-rolled: a tool-calling round trip, a
Chroma-backed lookup, and JSON-schema output — for one tool and one question. That
doesn't scale to real applications with many tools, longer loops, and provider
switching. LangChain exists to remove that repetition.

## Concept

LangChain is a framework of **standard interfaces** over the pieces from Phase 0:

- A standard interface for chat models (`init_chat_model` — any provider looks the
  same to your code)
- A standard interface for tools (`@tool` — plain Python function → callable the model
  can request)
- A standard interface for structured output (`with_structured_output` /
  `response_format`)
- A standard **agent runtime** (`create_agent`) that runs the request → execute →
  feed-back loop from Phase 0, Topic 04 — so you stop writing it by hand

```text
                    LangChain
        ┌───────────────┼───────────────┐
        ▼                ▼               ▼
   Chat Models         Tools        Agent Runtime
 (init_chat_model)   (@tool)        (create_agent)
        │                │               │
        └────────────────┴───────────────┘
                          │
                 same interface regardless
                 of which provider/tool/agent
                 shape you actually use
```

This is also where the wider ecosystem attaches:
- **LangGraph** (Phase 6) is the lower-level orchestration/runtime LangChain's agents
  are built on — reach for it directly when you need explicit control LangChain's
  agent runtime doesn't expose.
- **Deep Agents** (Phase 8) is a higher-level harness built on top of LangChain/LangGraph
  for long-running, planning-heavy tasks.
- **LangSmith** (Phase 9) is the tracing/evaluation/deployment layer that watches
  whatever you build with the above.

## Minimal code

`code.py` rebuilds the *shape* of Phase 0's tool-decision demo using LangChain's
`init_chat_model` and `@tool`, without an agent runtime yet (that's Topic 06) — so you
can compare it line-for-line against `phase-0-foundations/07-rag-vs-agent-vs-workflow/code.py`.

## Production notes

You do not have to use every layer. Plenty of production apps use only `init_chat_model`
+ prompts (no agent runtime at all) — pick the least amount of framework that solves the
problem, same principle as Phase 0 Topic 07's decision framework.

## Debugging

Import errors are the most common first friction point — LangChain is split across
several packages (`langchain`, `langchain-core`, `langchain-openai`,
`langchain-anthropic`, ...). If `pip install -r requirements.txt` was run at the repo
root, everything needed for this course is already installed.

## Mini challenge

Open `phase-0-foundations/07-rag-vs-agent-vs-workflow/code.py` side-by-side with this
topic's `code.py` and list every line of "plumbing" code that disappeared.
