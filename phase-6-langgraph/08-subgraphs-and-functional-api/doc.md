# 08 — Subgraphs & the Functional API

## Problem

Two separate problems show up once graphs get real: (1) a graph you built for one
workflow (say, "validate an order") is useful as a *step* inside a bigger graph, and
rebuilding it inline would duplicate logic; (2) sometimes the whole graph-of-nodes model
is more ceremony than a piece of logic needs — you just want checkpointing and resumption
around a couple of Python functions.

## Concept

**Subgraphs**: a compiled `StateGraph` can be added directly as a node in another graph
with `add_node`, as long as the two share the same state schema (or at least overlapping
keys) — no wrapper function required. The parent graph doesn't need to know the
subgraph's internals; it just sees one node that reads and writes the shared state.

```python
sub_builder = StateGraph(State)
sub_builder.add_node("validate", validate_fn)
...
subgraph = sub_builder.compile()

parent_builder = StateGraph(State)
parent_builder.add_node("validate_order", subgraph)   # a compiled graph AS a node
```

```text
parent graph
  START ─► validate_order [= compiled subgraph] ─► process_order ─► END
                  │
                  └─ internally: check_stock ─► check_payment ─► END (subgraph's own edges)
```

**Functional API**: `@entrypoint` + `@task` (from `langgraph.func`) give you the same
checkpointing/persistence/resumption machinery as `StateGraph`, but expressed as regular
Python functions and control flow instead of nodes and edges. `@task` marks a unit of
work (its result is cached per checkpoint, so resuming doesn't redo finished work);
`@entrypoint` marks the overall workflow function and turns it into a runnable object
with `.invoke()` / `.stream()`, just like a compiled graph.

```python
from langgraph.func import entrypoint, task

@task
def step_one(x: int) -> int:
    return x * 2

@entrypoint(checkpointer=InMemorySaver())
def workflow(x: int) -> int:
    return step_one(x).result()   # .result() blocks for the task's return value
```

Reach for the functional API when your "workflow" is naturally a straight-line (or
lightly branching) sequence of Python calls and you don't need to inspect/visualize it as
a graph; reach for `StateGraph` when the branching and node structure itself is something
you want to see, test, and reason about explicitly (most of this phase).

## Minimal code

`code.py` builds a small `validate_order` subgraph (two nodes: `check_stock`,
`check_payment`) composed into a parent `process_order` graph via `add_node`, then
re-implements Topic 02's 3-node pipeline (`greet` → `call_model` → `format_output`) as a
functional-API equivalent using `@entrypoint` / `@task`, so both styles produce
comparable output side by side.

## Production notes

Subgraphs are how large LangGraph systems stay maintainable — one team owns the
`validate_order` subgraph, another owns the parent checkout graph, and they only need to
agree on the shared state keys. The functional API is a good fit for background jobs and
pipelines that are more "do A, then B, then C, with retries and resumability" than
"branch based on live decisions."

## Debugging

- Subgraph's changes don't appear in the parent's final state → the two schemas don't
  actually share the key you expect; mismatched field names between parent and subgraph
  states are the most common cause.
- A `@task`-decorated function's result seems to run twice → you called the function but
  forgot `.result()` — the task call itself returns a future-like object immediately, it
  doesn't block.

## Mini challenge

Add a third node to the `validate_order` subgraph (e.g. `check_address`) and confirm the
parent graph's `process_order` node needs zero changes to pick up the new step.
