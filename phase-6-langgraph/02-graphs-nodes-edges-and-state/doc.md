# 02 — Graphs, Nodes, Edges & State

## Problem

Before building anything branching or persistent, you need the vocabulary. LangGraph
tutorials throw around "state," "node," and "edge" as if they're obvious — they're
simple, but only once you've seen the smallest possible graph run end to end.

## Concept

Three ideas, and that's genuinely most of it:

- **State** — a schema (a `TypedDict`) describing the data that flows through the graph.
  Every node reads from it and returns a partial update to it.
- **Node** — a plain Python function `(state) -> dict`. It receives the current state and
  returns only the keys it wants to change; LangGraph merges that into the running state.
- **Edge** — wiring between nodes (`add_edge(a, b)` means "after `a` finishes, run `b`").
  `START` and `END` are sentinel nodes marking where a graph begins and finishes.

```text
State: {"topic": str, "greeting": str, "reply": str, "final": str}

START ──► greet ──► call_model ──► format_output ──► END
           │            │                │
   sets "greeting"  sets "reply"   sets "final"
   (state in, partial dict out - each node only touches its own keys)
```

A graph is a `StateGraph(StateSchema)` builder: `add_node(name, fn)` registers each
function, `add_edge(...)` wires them in order, and `.compile()` turns the definition
into a runnable object. `.invoke(initial_state)` runs it start to finish and returns the
final merged state.

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    topic: str
    greeting: str

def greet(state: State) -> dict:
    return {"greeting": f"Let's talk about {state['topic']}."}

builder = StateGraph(State)
builder.add_node("greet", greet)
builder.add_edge(START, "greet")
builder.add_edge("greet", END)
graph = builder.compile()

graph.invoke({"topic": "LangGraph"})
# -> {"topic": "LangGraph", "greeting": "Let's talk about LangGraph."}
```

## Minimal code

`code.py` builds a 3-node pipeline — `greet` (deterministic) → `call_model` (one LLM
call) → `format_output` (deterministic) — wired with plain `add_edge` calls, no
branching yet (that's Topic 03). Printing the state after `.invoke()` shows every key
every node contributed, not just the last one.

## Production notes

Keep each node doing one thing you could describe in a sentence — a node that both calls
the model *and* decides where to route next is a sign it should be split into a model
node plus a conditional edge (Topic 03). Small nodes are also what makes `.stream()`
(Topic 05) and time travel (Topic 07) useful — each one is a distinct, inspectable step.

## Debugging

- `KeyError` inside a node → it's reading a state key no earlier node has set yet; check
  your edge order matches your data dependencies.
- A node's changes don't show up in the final state → make sure it *returns* a dict
  (`return {...}`); returning `None` or mutating `state` in place doesn't update anything.

## Mini challenge

Add a fourth node that runs after `format_output` and prints a word count of the
`"final"` field, wiring it in with a single `add_edge` call.
