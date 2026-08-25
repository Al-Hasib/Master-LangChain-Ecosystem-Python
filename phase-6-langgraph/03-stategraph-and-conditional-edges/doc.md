# 03 — StateGraph & Conditional Edges

## Problem

Topic 02's pipeline always runs the same three nodes in the same order — useful for
understanding the mechanics, useless for anything that needs to make a decision. A
support ticket isn't handled the same way regardless of what it's about; the graph needs
to look at the state and pick a path.

## Concept

`add_conditional_edges(source, router_fn, path_map)` adds a branch point: after `source`
finishes, `router_fn(state)` runs and returns a string key; `path_map` (a dict) says
which node that key leads to. This is the *entire* mechanism `create_agent`'s internal
`tools_condition` (Topic 01) uses — you're now writing the same kind of function
yourself, for your own routing logic instead of "does the model want a tool?".

```text
                     ┌──► billing_node   ──┐
START ──► classify ──┼──► technical_node ──┼──► END
                     └──► general_node   ──┘

router_fn(state) -> "billing" | "technical" | "general"
path_map = {"billing": "billing_node", "technical": "technical_node",
            "general": "general_node"}
```

```python
def route_by_category(state: State) -> str:
    return state["category"]  # must match a key in path_map

builder.add_conditional_edges(
    "classify",
    route_by_category,
    {"billing": "billing_node", "technical": "technical_node", "general": "general_node"},
)
```

The router function's only job is to read state and return a key — it should not call a
model or do real work itself (that belongs in a node). Every branch node still needs its
own edge onward (to another node, or to `END`) — `add_conditional_edges` only decides
which *one* path is taken next, it doesn't merge them back together for you.

## Minimal code

`code.py` extends Topic 02's shape with a `classify` node (one LLM call that outputs a
single category word) and three branch nodes (`billing_node`, `technical_node`,
`general_node`), each producing a different canned-but-branch-specific response, wired
with `add_conditional_edges`. This is the classify-then-route skeleton Topic 10's support
workflow builds on directly.

## Production notes

Keep the set of valid router outputs small and closed (an enum-like set of strings), and
have the node that produces the routed-on field (`classify` here) constrain the model's
output — free-text categories will eventually produce a key that isn't in your
`path_map` and crash the run. Phase 2's structured-output patterns are the fix.

## Debugging

- `KeyError` / graph hangs at a branch → the router function returned a string not
  present in `path_map`; log the router's return value on every call while developing.
- All branches behaving identically → double-check the router function is reading the
  field the classify node actually wrote, not a stale or misspelled key.

## Mini challenge

Add a fourth category (`"spam"`) that routes straight to `END` with no response at all,
and update the classify prompt so the model knows that option exists.
