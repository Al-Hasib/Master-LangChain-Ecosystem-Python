# 09 — Streaming Responses

## Problem

Every example so far waits for the full response before printing anything — fine for a
script, unacceptable for a chat UI where users expect text to appear as it's generated,
or a debugging session where you want to see an agent's steps as they happen, not just
the final answer.

## Concept

Two different things get called "streaming" and this course needs both:

- **Token streaming** — `model.stream(...)` yields chunks of a single response as the
  model generates it:

```python
for chunk in model.stream("Explain closures in Python."):
    print(chunk.text, end="", flush=True)
```

- **Agent step streaming** — `agent.stream(...)` yields updates as the *agent loop*
  progresses (a model call finished, a tool ran, ...), not just token-by-token text.
  Controlled by `stream_mode`:

```python
for step in agent.stream({"messages": [...]}, stream_mode="updates"):
    print(step)   # one entry per loop step: model call result, tool result, ...
```

`stream_mode="messages"` streams token-level chunks *from within* an agent run (so you
get both: which step you're in, and its tokens as they generate). `stream_mode="values"`
streams the full accumulated state after each step, rather than just the delta.

```text
model.stream()      : token, token, token, ...                (one LLM call)
agent.stream(...)   : step1-result, step2-result, ...          (whole loop)
  "messages" mode    : ...with token-level detail inside each step
```

## Minimal code

`code.py` streams a plain model response token-by-token, then streams a two-tool-call
agent run with `stream_mode="updates"` so each loop step prints as it happens instead of
only the final answer.

## Production notes

For a chat UI, stream at the token level to the frontend as soon as you have a model
response object — don't wait for `.invoke()` to fully resolve. For agent-backed UIs,
`stream_mode="updates"` (or `"messages"` for token-level detail) lets you show live
"thinking"/tool-use indicators, which meaningfully improves perceived latency.

## Debugging

- Streaming "works" but nothing prints until the end anyway → check you're actually
  iterating the stream (`for chunk in ...`) rather than materializing it into a list
  first, and that stdout isn't buffering (use `flush=True`).
- Agent stream shows steps but no token-level text → you're using `stream_mode="updates"`;
  switch to `"messages"` for token-level output during the agent run.

## Mini challenge

Measure and print the time-to-first-token vs. total response time for a `model.stream()`
call, to see concretely why streaming improves perceived latency even when total time is
unchanged.
