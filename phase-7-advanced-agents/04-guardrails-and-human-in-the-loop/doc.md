# 04 — Guardrails & Human-in-the-Loop Agents

## Problem

Phase 1 Topic 08 guarded the **input** side: reject a request before the model ever
sees it. That's half the job. Two failure modes it doesn't cover:

1. A tool returns something the *final answer* shouldn't repeat verbatim (a secret,
   an internal debug token) - the input was fine, the output isn't.
2. A tool is destructive enough (delete, refund, send) that it shouldn't fire without
   a human saying "yes, do it" - no wording of the input makes that safe to automate
   away entirely.

## Concept

**Output-side guardrail** — a check that runs *after* the model produces its final
answer, before that answer reaches the caller. There's no built-in "after the loop
ends" hook separate from the model call, so this uses `@after_model` (runs after every
model call) and only acts when the message has **no** `tool_calls` - i.e. it's the
final answer, not an intermediate step:

```python
import re
from langchain.agents.middleware import after_model
from langchain_core.messages import AIMessage

SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]+")

@after_model
def redact_secrets(state, runtime):
    last = state["messages"][-1]
    if last.tool_calls or not SECRET_PATTERN.search(str(last.content)):
        return None  # not a final answer, or nothing to redact
    cleaned = SECRET_PATTERN.sub("[REDACTED]", last.content)
    # Same message `id` -> the reducer REPLACES this message in place,
    # instead of appending a duplicate.
    return {"messages": [AIMessage(content=cleaned, id=last.id)]}
```

**Approval-required-before-tool-call** — a `@wrap_tool_call` middleware (Phase 1 Topic
08's retry pattern, repurposed) that checks *before* calling `handler(request)` whether
this specific tool call is allowed to proceed, and short-circuits with a rejection
`ToolMessage` if not:

```python
from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage

DANGEROUS_TOOLS = {"delete_user_record"}

@wrap_tool_call
def require_approval(request, handler):
    if request.tool_call["name"] in DANGEROUS_TOOLS and not request.runtime.context.approved:
        return ToolMessage(
            content="Blocked: this action requires human approval and none was given.",
            tool_call_id=request.tool_call["id"],
        )
    return handler(request)
```

In a real product, "approval" comes from a human clicking a button mid-run (that's what
LangGraph's `interrupt()` and `create_agent`'s `HumanInTheLoopMiddleware` are for -
they pause the graph and wait; see Phase 6 for the durable-execution machinery that
makes pausing/resuming possible). This topic's runnable code simulates the approval
decision via `runtime.context` so it stays a single-process, no-external-input script
you can run with `python code.py` - the gate logic (checking before calling `handler`)
is identical either way.

## Minimal code

`code.py` has two independent demos: (1) a tool that returns text containing a
fake secret token, with and without the `redact_secrets` output guardrail, showing the
raw vs. sanitized final answer; (2) a `delete_user_record` tool gated by
`require_approval`, invoked once with `approved=False` (blocked) and once with
`approved=True` (proceeds).

## Production notes

Keep output guardrails narrow and fast (regex/keyword checks) - an LLM-judge output
guardrail (Topic 09's pattern) is more powerful but adds latency and cost to *every*
response. For true human-in-the-loop (a person reviewing in a UI, not a hardcoded
context flag), use LangGraph's checkpointer + `interrupt()` so the run can pause for an
arbitrary amount of real time and resume exactly where it left off - not feasible with
a single Python process blocking on `input()`.

## Debugging

- Redaction middleware fires on intermediate tool-call messages too → you forgot the
  `if last.tool_calls: return None` guard - it should only touch the final answer.
- Approval gate blocks a call it shouldn't → check `request.tool_call["name"]` spelling
  matches the tool's function name exactly.
- Rejection message doesn't reach the model as an error the model can react to → make
  sure you return a `ToolMessage` (not raise/return a plain string) with a matching
  `tool_call_id`.

## Mini challenge

Add a second dangerous tool (e.g. `send_email`) to `DANGEROUS_TOOLS` and confirm one
`require_approval` middleware instance gates both without any per-tool code.
