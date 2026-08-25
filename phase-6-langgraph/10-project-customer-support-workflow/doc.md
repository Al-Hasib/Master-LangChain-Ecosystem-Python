# 10 — Project: Customer Support Workflow

## Problem

Time to combine everything this phase built separately: classify a ticket (Topic 03),
route it to a specialized handler (Topic 03), let that handler draft a response
(Topic 01/02), pause for a human to approve it before it goes out (Topic 06), and only
then respond — all as one inspectable, resumable graph instead of one opaque agent call.

## Concept

```text
                     ┌──► billing_agent    ──┐
START ─► classify ───┼──► technical_agent  ──┼──► human_approval ──approved?──► respond ──► END
                     └──► general_agent    ──┘         │
                                                        └──not approved──► respond (as "escalated")
```

Every piece here is a topic you've already built:

- `classify` — Topic 03's single-word-category node.
- conditional edges → one of three `*_agent` nodes — Topic 03's routing mechanism.
- each `*_agent` node — an LLM call producing a draft, scoped with a category-specific
  system context (Topic 02's `call_model` node, specialized per branch).
- `human_approval` — Topic 06's `interrupt()`, pausing the whole run until a human
  approves or rejects the draft.
- `respond` — a final deterministic node that finalizes the approved draft, or reports
  the ticket as escalated for human follow-up if rejected.

The graph is compiled with a checkpointer (Topic 04) — required for `interrupt()` to
work, and it's also what makes it safe for the "human approves" step to happen minutes or
hours after the draft was generated, in a completely different process.

## Minimal code

`code.py` builds the full graph above and runs two tickets end to end: one billing
question that gets approved (`Command(resume=True)`), one technical question that gets
rejected (`Command(resume=False)`) and ends up in the `respond` node's escalated branch —
each on its own `thread_id`.

## Production notes

In a real deployment, `human_approval`'s pause is where a support agent's dashboard would
show the draft and a approve/edit/reject control — the graph process can be completely
stateless between the pause and the resume, because the checkpointer (not the process)
holds the paused state (Topic 09). Swap the three `*_agent` nodes for `create_agent`
calls with real tools (order lookup, ticket history) when this stops being a demo.

## Debugging

- A ticket never reaches `human_approval` → check the routing keys from `classify`
  exactly match the `path_map` passed to `add_conditional_edges` (Topic 03's most common
  bug).
- Approval resumes but the response looks unrelated to the original ticket → the
  `human_approval` node restarted from its top on resume (Topic 06) — make sure nothing
  before its `interrupt()` call regenerates the draft with new, different output.

## Mini challenge

Add a fourth category, `"urgent"`, that skips `human_approval` entirely and goes straight
to `respond` — showing that human-in-the-loop is a per-branch decision, not a
whole-graph one.
