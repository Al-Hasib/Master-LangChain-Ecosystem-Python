# 01 — Agent Architecture & Tool-Calling Agents

## Problem

Phase 1 Topic 06 introduced `create_agent` and printed a message trace, but the examples
only ever needed **one** tool call before answering. Real tasks chain tools — the
answer to step 2 depends on the result of step 1. If you can't read a multi-step trace
fluently, every agent bug past this point looks like a black box. This topic re-opens
the loop `create_agent` hides and makes multi-step tool chaining legible before we add
memory, guardrails, and planning on top of it.

## Concept

`create_agent` is a prebuilt loop (itself a small LangGraph graph under the hood — more
on that in Phase 6): call the model → if it asked for tool(s), run them and append
`ToolMessage`s → call the model again with the updated history → repeat until the model
replies with **no** tool calls. That final, tool-call-free `AIMessage` is the answer.

```text
 [HumanMessage]
      │
      ▼
 ┌─────────┐   tool_calls present   ┌───────────┐
 │  model  │ ──────────────────────▶│   tools   │
 └─────────┘                        └───────────┘
      ▲                                   │
      │           ToolMessage(s)          │
      └───────────────────────────────────┘
      │
      │ no tool_calls
      ▼
 [AIMessage]  <- final answer
```

Each trip around that circle is one **loop iteration**. A question that needs two facts
looked up in sequence (fact B depends on fact A) takes at least two iterations — two
separate `AIMessage`s with `tool_calls`, two `ToolMessage`s, then a final `AIMessage`.

## Minimal code

`code.py` gives the agent two tools that must be called **in order**:
`lookup_user_city` (name → city) and `get_weather` (city → forecast). The question
("What's the weather where Priya lives?") can't be answered in one tool call — the
model doesn't know Priya's city until `lookup_user_city` returns it. The script prints
the full message trace annotated by loop iteration, so you can see the two round trips.

## Production notes

`create_agent` is great until you need: a human-approval checkpoint mid-loop, resuming
a run after a crash, branching to different tool sets based on state, or streaming
intermediate node output. That's precisely what LangGraph (Phase 6) is for — it's the
same agent loop, but built explicitly out of nodes and edges so you can insert, inspect,
or persist any point in it. Reach for `create_agent` first; drop to LangGraph when you
need control the loop doesn't expose.

## Debugging

- Loop never terminates / hits a recursion limit → the model keeps requesting tools
  because a tool's return value doesn't actually answer what it was asked; check the
  tool's docstring and return format.
- Wrong tool called first → tool docstrings are the model's only signal for *when* to
  use a tool — vague docstrings cause misordered calls in chained scenarios.
- Trace shows a `ToolMessage` with an error string instead of raising → tools that
  raise exceptions surface as an error `ToolMessage` by default so the model can react;
  that's usually what you want, not a Python crash.

## Mini challenge

Add a third tool, `get_clothing_suggestion(forecast: str)`, that only makes sense to
call after `get_weather` returns. Confirm the trace now shows three loop iterations.
