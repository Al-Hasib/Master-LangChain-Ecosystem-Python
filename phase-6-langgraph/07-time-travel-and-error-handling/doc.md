# 07 — Time Travel & Error Handling

## Problem

Two different failure modes need two different tools. "This node sometimes fails
transiently (a flaky API)" needs a retry. "This run produced a wrong result three steps
in and I need to see exactly what state it had at that point" needs a way to look at —
and rerun from — the past. A checkpointer (Topic 04) already stores enough history to
do both.

## Concept

**Time travel**: `graph.get_state_history(config)` returns every checkpoint saved for a
thread, most recent first, each one a `StateSnapshot` with the state and a
`checkpoint_id`. Pass that `checkpoint_id` back in `config` and invoke again — LangGraph
resumes from *that exact point*, skipping everything before it and re-running everything
after (this is also how you'd fork a run to explore "what if node X had produced a
different result").

```python
config = {"configurable": {"thread_id": "run-1"}}
history = list(graph.get_state_history(config))     # newest first

past_checkpoint = history[2].config                 # pick an earlier point
graph.invoke(None, past_checkpoint)                  # replays from there
```

```text
checkpoint history (newest first):
[3] after format_output   <- current
[2] after call_model
[1] after greet           <- replay from here: greet's result is reused,
[0] before greet              call_model + format_output RE-RUN from this state
```

**Retry on node failure**: `add_node(..., retry_policy=RetryPolicy(...))` retries the
*whole node* automatically on exceptions that match its `retry_on` predicate, with
backoff between attempts — no manual `try/except` loop needed inside the node itself.

```python
from langgraph.types import RetryPolicy

builder.add_node(
    "flaky_step", flaky_step,
    retry_policy=RetryPolicy(max_attempts=3, retry_on=(RuntimeError,)),
)
```

## Minimal code

`code.py` runs Topic 02's 3-node pipeline once, lists its checkpoint history with
`get_state_history`, then re-invokes from the checkpoint right after `greet` to show
`call_model` and `format_output` re-running from that earlier point. Separately, it adds
a node that fails its first two calls, wired with a `RetryPolicy`, and shows it succeed
on the third attempt without any manual retry code.

## Production notes

Time travel is a debugging and "what-if" tool, not a normal runtime path — use it in a
notebook or admin tool to inspect a bad run, not as part of your live request path.
`RetryPolicy`'s default `retry_on` deliberately excludes bugs like `ValueError` /
`TypeError` (retrying a programming error just wastes time) — scope `retry_on` to the
specific transient exceptions a node can actually raise.

## Debugging

- Replay produces identical output every time → the node(s) after your replay point are
  deterministic (no LLM call, no randomness); that's expected, not a bug — replay a point
  before an LLM call to see genuine variation.
- `RetryPolicy` doesn't seem to retry → check the raised exception type is actually
  covered by `retry_on`; an uncovered exception type propagates immediately.

## Mini challenge

Pick a checkpoint from *before* `call_model` in the history list, use `update_state` to
change the `topic` field, then invoke from that forked config — confirm the rest of the
run reflects your edited value, not the original.
