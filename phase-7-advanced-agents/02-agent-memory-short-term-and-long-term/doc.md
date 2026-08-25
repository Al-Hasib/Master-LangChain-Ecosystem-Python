# 02 — Agent Memory: Short-Term & Long-Term

## Problem

Phase 1 Topic 07 showed `result["messages"]` as agent **state** - but that list only
lives for the duration of one Python process holding one `agent.invoke()` chain. Start
a brand-new conversation (a fresh `messages` list, maybe even a fresh process) and the
agent has no idea it ever talked to this user before. A support bot that forgets a
customer's stated preference every single session is not usable. We need memory that
survives past the message list.

## Concept

LangChain/LangGraph draws a hard line between two kinds of memory:

- **Short-term memory** — the message list itself (Phase 1 Topic 07). Scoped to one
  conversation/thread. Already covered — nothing new here.
- **Long-term memory** — a separate key-value **`Store`**, scoped to whatever you
  choose (a user, an org, globally), that survives across completely separate
  `agent.invoke()` calls. LangGraph ships `InMemoryStore` (`langgraph.store.memory`)
  for this. Pass it to `create_agent(..., store=...)`; tools read/write it through
  `runtime.store` — the exact same dependency-injection pattern as `runtime.context`
  from Phase 1 Topic 07, except `runtime.store` is **read/write** and the model never
  sees its contents either way.

```python
from langgraph.store.memory import InMemoryStore
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime

store = InMemoryStore()

@tool
def save_preference(preference: str, runtime: ToolRuntime) -> str:
    """Remember a user preference for future conversations."""
    runtime.store.put(("preferences",), "units", preference)
    return "Saved."

@tool
def get_preference(runtime: ToolRuntime) -> str:
    """Recall a previously saved user preference, if any."""
    item = runtime.store.get(("preferences",), "units")
    return item.value if item else "No preference saved yet."

agent = create_agent(model="gpt-4o-mini", tools=[save_preference, get_preference], store=store)
```

Data is namespaced by a tuple (like nested folders) plus a key — `("preferences",)` /
`"units"` above. Namespace by user (e.g. `(user_id, "preferences")`) in any app with
more than one user, or every user shares the same memory.

```text
Conversation 1 (agent.invoke #1)          Conversation 2 (agent.invoke #2, LATER)
  messages: [fresh list]                    messages: [fresh list - NEW conversation]
       │                                          │
       ▼                                          ▼
  save_preference tool ──► store.put ───────► store.get ──► get_preference tool
                              (the Store object outlives both invoke() calls)
```

## Minimal code

`code.py` builds one `InMemoryStore`, gives an agent a `save_preference` and a
`get_preference` tool, then makes **two separate `agent.invoke()` calls with two
separate, unrelated `messages` lists** - simulating two different conversations. The
first states and saves a preference; the second, with zero shared message history,
correctly recalls it - proof the memory lived in the store, not the message list.

## Production notes

`InMemoryStore` lives only for the lifetime of the Python process - it is a teaching
stand-in, not persistence across restarts. Production long-term memory swaps in a
database-backed `BaseStore` implementation (e.g. a Postgres-backed store) so memory
survives deploys and restarts; the tool code (`runtime.store.get`/`.put`) does not
change at all - only the object passed to `store=` does. Always namespace by user/tenant
ID to avoid leaking one user's saved facts into another user's conversation.

## Debugging

- `runtime.store` is `None` inside a tool → you forgot to pass `store=` to
  `create_agent`.
- `store.get(...)` returns `None` when you expected a value → namespace tuple or key
  string doesn't match exactly what `.put()` used - these are exact-match, not fuzzy.
- Memory "leaks" between users → you used a single flat namespace instead of
  including the user/tenant ID in it.

## Mini challenge

Add a second namespace, e.g. `(user_id, "facts")`, and a `save_fact` tool that stores
arbitrary free-text facts under it, separate from the `units` preference.
