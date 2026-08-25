# 01 — Why LangGraph? (LangChain vs LangGraph)

## Problem

Phase 1 Topic 06's `create_agent` gave you a working request → execute tool → feed
result back → repeat loop for free. That's exactly the point — until you hit something
it doesn't expose: forcing a specific step order regardless of what the model wants to
do next, persisting state across a process restart, pausing before a sensitive step for
a human to approve, or replaying a run from a specific past point to debug it. Phase 1's
loop is a black box on purpose; there's no lever inside it for any of that.

## Concept

`create_agent` isn't a different technology from what you're about to learn — it's a
thin, opinionated **StateGraph** underneath. It fixes the shape for you: one node calls
the model, a conditional edge checks "did it ask for a tool?", a tools node runs the
tool(s), and an edge sends control back to the model node — looping until the model
stops requesting tools.

**LangGraph is that same graph, but you draw it.** Nodes are plain functions, edges are
wiring you write explicitly, and branching is a function you control — so anything
`create_agent` hardcodes (loop shape, when to stop, what happens around each step)
becomes something you can change.

```text
create_agent(model, tools)                    the SAME loop, built by hand in LangGraph
┌─────────────────────────┐                   ┌─────────────────────────────────┐
│   (hidden StateGraph)    │                   │  builder.add_node("agent", ...)  │
│                          │                   │  builder.add_node("tools", ...)  │
│   agent ──tool_calls?──► tools               │  builder.add_edge(START,"agent") │
│     ▲                     │                   │  builder.add_conditional_edges(  │
│     └─────────────────────┘                   │      "agent", tools_condition)   │
│   no tool_calls → END     │                   │  builder.add_edge("tools","agent")│
└─────────────────────────┘                   └─────────────────────────────────┘
     opaque, fixed shape                             every wire is yours to change
```

You don't need LangGraph for every agent — most of Phase 1's examples are genuinely
simpler with `create_agent`. Reach for LangGraph directly once you need: deterministic
step order the model can't override (Topic 03), durable persistence across restarts
(Topic 04), a human-approval pause (Topic 06), replay/time-travel for debugging
(Topic 07), or composing several specialized graphs together (Topic 08).

## Minimal code

`code.py` builds the *same* one-tool question two ways: first with `create_agent`
(Phase 1 style, opaque loop), then as a hand-built two-node `StateGraph` using
`ToolNode` and `tools_condition` from `langgraph.prebuilt` — proving they're the same
idea at different altitudes, not two unrelated frameworks.

## Production notes

Most teams start with `create_agent` and only drop to raw LangGraph for the specific
part of the system that needs the extra control (e.g. the approval step in a support
workflow, Topic 10) — you can mix both in one codebase; a LangGraph node can itself call
a `create_agent` agent internally.

## Debugging

- If you're fighting `create_agent`'s middleware hooks (Phase 1 Topic 08) trying to force
  a specific order, that's usually a sign you actually want a plain `StateGraph` instead
  of more middleware.
- A hand-built graph that never reaches `END` almost always means a conditional edge
  function returns a routing key that isn't wired to any node — check the path map.

## Mini challenge

Add a second tool to the hand-built graph version and confirm `tools_condition` still
routes correctly to the `tools` node without touching the conditional edge logic itself.
