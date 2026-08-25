# 03 — Planning & Todo Lists

## Problem

On a genuinely multi-step task, a model without an explicit plan tends to either skip
steps, redo steps it already finished, or lose track of what "done" means — because the
only record of progress is buried in a growing message history.

## Concept

Deep Agents ships a purpose-built planning tool, `write_todos`, but — as of `deepagents`
0.7 — it's **opt-in**, not bound by default (confirmed via
[docs.langchain.com/oss/python/deepagents/middleware](https://docs.langchain.com/oss/python/deepagents/middleware):
*"Starting in v0.7 task planning is opt-in only. In earlier versions, task planning
middleware was included by default."*). You turn it on with `TodoListMiddleware`, which
actually lives in core LangChain (not deepagents itself) at
`langchain.agents.middleware` — the same middleware works with plain `create_agent` too:

```python
from langchain.agents.middleware import TodoListMiddleware
from deepagents import create_deep_agent

agent = create_deep_agent(
    model=model,
    tools=[...],
    middleware=[TodoListMiddleware()],
)
```

Once bound, the model gets a `write_todos` tool it can call to **replace the entire todo
list** in one call (each item has `content` + a `status` of `pending` / `in_progress` /
`completed`) — replacing the whole list, not appending, is deliberate: it keeps the plan
a single source of truth instead of an ever-growing, possibly-stale log. The list is
stored in graph state, so `agent.invoke(...)`'s return value carries a `"todos"` key you
can inspect after the run — no need to dig through the message trace to see the final
plan state.

```text
user request
     │
     ▼
write_todos([...])   <- model plans BEFORE acting
     │
     ▼
step 1 (tool call) ──> write_todos([step1: done, step2: in_progress, ...])
     │
     ▼
step 2 (tool call) ──> write_todos([...all done...])
     │
     ▼
final answer
```

## Minimal code

`code.py` gives a deep agent `TodoListMiddleware` plus a couple of small research-style
tools, asks it a task explicitly framed as multiple steps, and prints `result["todos"]`
after the run alongside every `write_todos` call seen in the message trace — showing the
plan evolve turn by turn.

## Production notes

Planning pays off most on tasks with 4+ genuinely distinct steps, or with weaker/cheaper
models that benefit from an explicit accountability tool (per the docs' own guidance).
For a 1-2 step task, it's pure overhead — skip it.

## Debugging

If `result.get("todos")` comes back empty even though the task was multi-step, confirm
`TodoListMiddleware()` is actually in the `middleware=[...]` list passed to
`create_deep_agent` — it is not bound automatically.

## Mini challenge

Ask the agent a task where you explicitly tell it NOT to use a todo list and see whether
it still calls `write_todos` — models sometimes call a bound tool out of habit even when
told not to, which is a useful failure mode to see once.
