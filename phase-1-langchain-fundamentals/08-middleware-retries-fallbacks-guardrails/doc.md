# 08 — Middleware, Retries, Fallbacks & Guardrails

## Problem

Real agents need behavior around the loop, not just in it: block certain inputs before
they reach the model, retry a flaky tool call, fall back to a second model if the first
errors out. Rewriting the agent loop (Topic 06 hid it from you on purpose) to add these
would be a step backward. Middleware hooks into the loop without rewriting it.

## Concept

**Middleware** are functions that run at specific points in the agent loop —
`create_agent(..., middleware=[...])`:

- `@before_model` — runs before each model call; can inspect/modify state, or short
  circuit the loop entirely (`return {"jump_to": "end"}`).
- `@wrap_tool_call` — wraps each tool execution; can retry, log, or transform results.
- Built-ins exist too, e.g. `SummarizationMiddleware` (trims long history),
  `HumanInTheLoopMiddleware` (pause for approval before specific tools — previewed here,
  covered fully in Phase 6/7).

```python
from langchain.agents.middleware import before_model, wrap_tool_call

@before_model
def block_banned_words(state, runtime):
    """A simple guardrail: refuse to process input containing banned terms."""
    last = state["messages"][-1]
    if any(word in last.content.lower() for word in ["password", "secret"]):
        return {"jump_to": "end"}
    return None

@wrap_tool_call
def retry_on_tool_error(request, handler):
    """Retry a failing tool up to 3 times before giving up."""
    for attempt in range(3):
        try:
            return handler(request)
        except Exception:
            if attempt == 2:
                raise

agent = create_agent(model="gpt-4o-mini", tools=[...], middleware=[block_banned_words, retry_on_tool_error])
```

**Fallbacks** are a model-level concern, not middleware: `model.with_fallbacks([backup_model])`
tries the primary model and falls back to another on failure (auth error, rate limit,
timeout).

## Minimal code

`code.py` builds an agent with a `before_model` guardrail (blocks a banned word) and a
`wrap_tool_call` retry wrapper around a tool that fails on its first two calls by
design, then succeeds — proving the retry logic runs without any change to the tool or
the agent loop itself.

## Production notes

Order matters when you have multiple middleware — they run in the list order you
provide. Keep guardrail middleware cheap (no LLM calls) where possible, since it runs on
every single loop iteration.

## Debugging

- Guardrail middleware silently doesn't fire → check the return contract: returning
  `None` means "continue normally," only specific dict shapes (like `{"jump_to": "end"}`)
  change control flow.
- Retry wrapper retries forever / never gives up → make sure the final attempt
  re-raises instead of swallowing the exception.

## Mini challenge

Add a second `before_model` middleware that logs the message count on every loop
iteration, and observe both middleware running together in the list order you gave.
