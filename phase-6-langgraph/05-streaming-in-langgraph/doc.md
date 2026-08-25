# 05 — Streaming in LangGraph

## Problem

`.invoke()` blocks until the whole graph finishes, then hands back the final state in one
shot. Phase 1 Topic 09 solved this at the single-model-call level with `.stream()` on a
chat model; a multi-node graph needs the same idea one level up — watching progress
*node by node*, not just token by token inside one call.

## Concept

`graph.stream(input, config, stream_mode=...)` yields output as the run progresses. The
`stream_mode` argument changes what each yielded chunk looks like — the same parameter
name and several of the same values as Phase 1 Topic 09's model-level streaming:

- `"updates"` — after each node finishes, yield only `{node_name: {partial state it
  returned}}`. Cheapest, most common for "show progress" UIs.
- `"values"` — after each node finishes, yield the **entire** accumulated state so far.
  Useful when downstream code just wants "the latest full picture."
- `"messages"` — token-by-token LLM output from inside any node, as `(token, metadata)`
  pairs, mirroring Phase 1 Topic 09's chat-model streaming but tagged with which node
  produced it.

```text
graph.stream(input, stream_mode="updates")
   yields: {"classify": {"category": "billing"}}         <- only classify's own update
   yields: {"billing_node": {"response": "..."}}          <- only billing_node's update

graph.stream(input, stream_mode="values")
   yields: {"message": "...", "category": "billing", "response": ""}      <- after classify
   yields: {"message": "...", "category": "billing", "response": "..."}   <- after billing_node
```

```python
for chunk in graph.stream({"message": "..."}, stream_mode="updates"):
    print(chunk)   # {"classify": {"category": "billing"}}, then next node, ...
```

You can pass a list of modes (`stream_mode=["updates", "messages"]`) to get both
interleaved, each chunk tagged with which mode it came from — handy for a UI that shows
both a progress indicator and live token output.

## Minimal code

`code.py` reuses Topic 03's classify-then-route graph and streams the same run twice:
once with `stream_mode="updates"` (prints each node's contribution as it happens) and
once with `stream_mode="values"` (prints the full accumulated state after each node).

## Production notes

`"updates"` is almost always what a progress UI wants — it's the smallest payload and
maps directly to "step N just finished, here's what it produced." Reserve `"values"` for
cases where you genuinely need the full state at every step (e.g. writing intermediate
checkpoints somewhere yourself). `"messages"` is what you'd wire to a chat UI that shows
the model's answer appearing token by token.

## Debugging

- Nothing is printed until the whole run finishes → you're iterating a `.stream()` call
  but accidentally collecting it into a list first (`list(graph.stream(...))`) instead of
  iterating directly in the `for` loop.
- `"messages"` mode yields nothing → the node in question isn't making a streamable LLM
  call the graph can see into (e.g. it's calling `.invoke()` deep inside a helper that
  LangGraph can't attribute back to a node).

## Mini challenge

Add `stream_mode=["updates", "messages"]` to one call and print which mode each chunk
came from, to see both progress events and token-level output interleaved.
