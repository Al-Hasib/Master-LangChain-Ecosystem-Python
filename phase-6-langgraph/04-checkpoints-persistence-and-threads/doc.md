# 04 — Checkpoints, Persistence & Threads

## Problem

Every graph so far forgets everything the instant `.invoke()` returns — call it twice and
the second call has no idea the first one happened. Real conversations and workflows need
state to survive between calls (and, eventually, between process restarts).

## Concept

Compile a graph with a **checkpointer** and it saves the full state after every node
finishes. Each saved history is keyed by a **thread ID** you pass in `config` — same
thread ID on the next call, and the graph picks up exactly where it left off; a
different thread ID starts from nothing, completely isolated.

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()          # dev/demo only - lives in RAM, lost on restart
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "user-1"}}
graph.invoke({"messages": [...]}, config)   # turn 1 - saved under "user-1"
graph.invoke({"messages": [...]}, config)   # turn 2 - resumes from turn 1's state
```

```text
thread_id="user-1"          thread_id="user-2"
   turn 1 ──► checkpoint        turn 1 ──► checkpoint
   turn 2 ──► checkpoint           (never sees user-1's history)
      (each turn sees everything saved under THIS thread_id only)
```

`InMemorySaver` (from `langgraph.checkpoint.memory`) is the in-process, RAM-only
checkpointer — perfect for development, gone the moment the process exits. Production
swaps it for a durable backend (Postgres, SQLite, Redis-backed) without touching a single
node — the checkpointer is a compile-time argument, not part of the graph's logic.

## Minimal code

`code.py` compiles a one-node chat graph (`MessagesState` + a model call) with
`InMemorySaver`, then: two calls on `thread_id="user-1"` where the second call proves the
model remembers the first ("My name is Alice" → later "What's my name?"), followed by one
call on a fresh `thread_id="user-2"` asking the same follow-up to show it has no memory of
`user-1`'s conversation at all.

## Production notes

`thread_id` is your unit of isolation — one per end-user conversation, one per background
job run, whatever makes sense for your app; never share a thread_id across unrelated
users. Swapping `InMemorySaver` for a real backend (e.g. `PostgresSaver` from
`langgraph-checkpoint-postgres`) is the single change needed to survive a restart —
covered as a call-out here, installed only if you're actually deploying (Topic 09).

## Debugging

- State "resets" every call → you forgot to compile with a `checkpointer`, or you're
  generating a new `thread_id` each time instead of reusing one.
- Two users see each other's data → you're reusing one `thread_id` for every request
  (a common bug: hardcoding it instead of deriving it from session/user identity).

## Mini challenge

Add a third call on `thread_id="user-1"` asking "What have we talked about?" and confirm
the model can reference both earlier turns — the whole thread's history, not just the
last one.
