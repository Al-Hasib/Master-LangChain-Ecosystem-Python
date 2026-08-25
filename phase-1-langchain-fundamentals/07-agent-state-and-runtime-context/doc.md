# 07 — Agent State & Runtime Context

## Problem

Real tools need information that shouldn't come from the model at all — a `user_id`,
a request-scoped API token, a tenant ID for multi-tenant apps. Putting these in the
prompt is unsafe (the model could leak or "forget" them) and wasteful. LangChain
separates **state** (what's tracked as the agent runs) from **context** (config injected
per invocation, never seen by the model).

## Concept

- **State** — `result["messages"]` from Topic 06 *is* the agent's state: the running
  list of messages. Every step reads and appends to it. State is what makes the loop
  resumable/inspectable.
- **Runtime context** — data your application supplies per `invoke()` call that tools
  can read but the **model never sees** (it's excluded from what's sent to the LLM).
  Defined as a dataclass, declared on the agent via `context_schema`, passed at call
  time via `context=`:

```python
from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent

@dataclass
class Context:
    user_id: str

@tool
def get_account_balance(runtime: ToolRuntime[Context]) -> str:
    """Get the current user's account balance."""
    user_id = runtime.context.user_id       # never sent to the model
    return f"Balance for {user_id}: $1,204.50"

agent = create_agent(model="gpt-4o-mini", tools=[get_account_balance], context_schema=Context)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my balance?"}]},
    context=Context(user_id="user_123"),
)
```

The `runtime: ToolRuntime[Context]` parameter is invisible to the model's tool schema —
it's dependency injection for your tool's Python code, not something the LLM fills in.

## Minimal code

`code.py` defines a `Context` dataclass carrying a `user_id`, a tool that uses it to
look up a per-user fact from a small in-memory dict, and confirms two different
`context=` values produce different tool results for the identical question — proving
the model never controls this value.

## Production notes

Use runtime context for anything security- or tenant-sensitive: auth tokens, tenant
IDs, feature flags. Never put secrets in the system prompt or in a tool argument the
model fills in — the model could echo them into a final answer.

## Debugging

- `TypeError` about missing `context` at `invoke()` → you declared `context_schema` but
  forgot to pass `context=` at call time.
- Tool can't find `runtime.context` → the tool's parameter isn't correctly typed as
  `ToolRuntime[YourContextClass]`.

## Mini challenge

Add a second field to `Context` (e.g. `is_premium_user: bool`) and have the tool return
different information depending on it.
