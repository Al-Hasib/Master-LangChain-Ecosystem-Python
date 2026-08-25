# 03 — Context Management & Middleware

## Problem

Every message ever exchanged gets re-sent to the model on every loop iteration
(Topic 01's diagram). A long-running conversation - or an agent that racks up many
tool calls - eventually blows past the context window, gets slower, and gets more
expensive, even though the model only needs the *recent* and *relevant* parts of the
history to answer the next question.

## Concept

This is a **context management** problem, and it's solved the same way Phase 1 Topic 08
solved guardrails and retries: with `@before_model` middleware that runs before every
model call and can rewrite the message list that's about to be sent.

The one subtlety: `state["messages"]` uses an *additive* reducer (`add_messages`) -
returning `{"messages": [...]}` from middleware does **not** replace the list, it merges
into it by message `id`. To actually shrink history you emit `RemoveMessage(id=...)`
for the messages you want dropped; the reducer deletes exactly those by id.

```python
from langchain_core.messages import RemoveMessage
from langchain.agents.middleware import before_model

KEEP_LAST_N = 6

@before_model
def trim_to_last_n(state, runtime):
    messages = state["messages"]
    if len(messages) <= KEEP_LAST_N:
        return None  # nothing to trim
    to_drop = messages[:-KEEP_LAST_N]
    return {"messages": [RemoveMessage(id=m.id) for m in to_drop]}
```

```text
state["messages"]:  [m1] [m2] [m3] [m4] [m5] [m6] [m7] [m8]
                      └──── dropped via RemoveMessage ────┘  └── kept (last N) ──┘
```

For production-grade summarization (condense old messages into a synopsis instead of
deleting them outright), LangChain ships a built-in `SummarizationMiddleware`
(`from langchain.agents.middleware import SummarizationMiddleware`) that watches token
count and, past a threshold, replaces older messages with an LLM-generated summary
while keeping the most recent messages verbatim:

```python
from langchain.agents.middleware import SummarizationMiddleware

SummarizationMiddleware(
    model="gpt-4o-mini",           # can be cheaper/smaller than the main agent model
    trigger=("messages", 20),      # summarize once history exceeds 20 messages
    keep=("messages", 6),          # always keep the last 6 messages verbatim
)
```

(`trigger`/`keep` also accept `("tokens", N)` or `("fraction", 0.x)` of the context
window - verified against the installed `langchain` package's current signature.)

## Minimal code

`code.py` hand-rolls `trim_to_last_n` (reliable, zero extra model calls, easy to reason
about) as the primary demo: it seeds a conversation with many prior turns, runs it
through the agent, and prints the message count before and after the middleware fires
to prove the history actually shrank. A second, smaller block builds a second agent
using the real `SummarizationMiddleware` to confirm the built-in import and constructor
work as documented above.

## Production notes

Prefer trimming (cheap, deterministic) for high-volume/low-stakes agents; prefer
summarization (costs one extra LLM call, preserves more meaning) when losing older
context would break correctness - e.g. a long troubleshooting session where an early
detail still matters. Never trim/summarize away the system prompt.

## Debugging

- History doesn't shrink after your `before_model` middleware runs → you returned a
  plain trimmed list instead of `RemoveMessage(id=...)` for the dropped messages - the
  additive reducer silently ignores messages that were simply left out.
- `RemoveMessage` raises/does nothing → the `id` you passed doesn't match an existing
  message's `id` exactly.
- `SummarizationMiddleware` never fires → your `trigger` threshold is higher than the
  conversation ever reaches in the demo; lower it to see it activate.

## Mini challenge

Change `KEEP_LAST_N` to 2 and re-run - watch the agent lose earlier context and
potentially answer a follow-up question incorrectly, then dial it back up.
