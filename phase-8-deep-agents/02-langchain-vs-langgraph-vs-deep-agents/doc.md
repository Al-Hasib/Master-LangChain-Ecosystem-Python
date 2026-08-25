# 02 — LangChain vs LangGraph vs Deep Agents

## Problem

Three names get used almost interchangeably by newcomers, which makes it hard to know
which one to reach for. Picking the wrong layer means either fighting an overly rigid
tool-calling loop, or hand-building orchestration a higher layer already gives you for
free.

## Concept

Three layers, same underlying execution engine:

```text
LangChain  (Phase 1)     create_agent()      - a ready-made tool-calling loop
     │                        built on
     ▼
LangGraph  (Phase 6)     StateGraph          - explicit nodes/edges/state you control directly
     │                        built on
     ▼
Deep Agents (Phase 8)    create_deep_agent() - LangGraph graph + planning/filesystem/subagent harness
```

- LangChain's `create_agent` = "give me tools and a model, run the loop for me." Best
  default for most agents (Phase 1).
- LangGraph's `StateGraph` = "let me define the exact nodes, edges, and state
  transitions" (Phase 6 owns this in depth) — reach for it when you need precise control:
  conditional branching, human-approval steps, persistence across restarts.
- Deep Agents' `create_deep_agent` = "give me a `create_agent`-shaped loop, but
  pre-wired with the specific add-ons long-horizon tasks need" (Topic 01) — it *compiles
  to* a LangGraph graph (confirmed: `create_deep_agent` returns a `CompiledStateGraph`,
  per
  [reference.langchain.com/python/deepagents/graph/create_deep_agent](https://reference.langchain.com/python/deepagents/graph/create_deep_agent)),
  so everything you learn about LangGraph in Phase 6 (streaming, checkpointing, the
  `checkpointer=`/`store=` params) applies to a deep agent too.

None of these are mutually exclusive: a deep agent's `task` tool spawns subagents that
are themselves just more agents, and a deep agent can be embedded as one node inside a
larger LangGraph graph (Topic 07).

## Minimal code

`code.py` constructs "the same" simple agent three ways: a real `create_agent` call, a
real `create_deep_agent` call, and a **commented, illustrative-only** `StateGraph` sketch
(Phase 6 is the authority on real LangGraph code — this file doesn't want to
misrepresent that API). Running the file shows the two real agents answer the same
question so the layering is visually concrete, not just described.

## Production notes

Default to `create_agent`. Move to explicit LangGraph when you need control the loop
doesn't give you. Move to Deep Agents when the task is long-horizon regardless of how
much manual control you want (Topic 08 gives the fuller decision framework).

## Debugging

If you're not sure which layer you're looking at in someone else's code, check the
import: `langchain.agents.create_agent`, `langgraph.graph.StateGraph`, or
`deepagents.create_deep_agent` — the import alone tells you the layer.

## Mini challenge

Trace what `create_deep_agent` returns (`type(agent)`) and compare it to what Phase 6's
`StateGraph(...).compile()` returns — confirm they're the same family of object.
