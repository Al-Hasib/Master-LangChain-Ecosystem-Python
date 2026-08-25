# 06 — Human-in-the-Loop & Interrupts

## Problem

Some steps are too risky to let an agent run unattended — sending an email, charging a
card, deleting a record. You want the graph to do everything up to that point, stop, show
a human what it's about to do, and only continue once someone says yes.

## Concept

Calling `interrupt(payload)` inside a node **pauses the entire graph run** at that exact
point and surfaces `payload` to whoever is running it. The run doesn't crash and it isn't
"done" — it's paused, and its state is saved (this is why interrupts *require* a
checkpointer, Topic 04). To continue, invoke the graph again on the same `thread_id` with
`Command(resume=value)` — `value` becomes `interrupt(...)`'s return value inside the node,
and execution continues from there.

```python
from langgraph.types import interrupt, Command

def human_approval(state: State) -> dict:
    approved = interrupt({"question": "Send this email?", "draft": state["draft"]})
    return {"approved": approved}
```

```text
graph.invoke(input, config)
      │
      ▼
  draft_email ──► human_approval ──interrupt()──► (PAUSED, state saved)
                                                          │
                                        human reviews the payload
                                                          │
graph.invoke(Command(resume=True), config) ──────────────┘
      │
      ▼
  human_approval resumes, approved=True ──► send_email ──► END
```

Two things catch people out: the node **restarts from the top** on resume (any code
before the `interrupt()` call in that node runs again — keep it side-effect-free), and
the graph **must** be compiled with a checkpointer, or there's nowhere to save the paused
state and resuming fails.

## Minimal code

`code.py` builds `draft_email` (LLM writes a short draft) → `human_approval` (calls
`interrupt(...)` with the draft) → conditional edge → `send_email` (simulated) or
`cancelled`. One run shows the pause-then-approve path (`Command(resume=True)`); a second
run on a fresh thread shows pause-then-reject (`Command(resume=False)`).

## Production notes

In a real app the "human reviews the payload" step is a UI (or a Slack message, or a
queue) that eventually calls your backend with the resume decision — the graph process
itself can shut down entirely while paused, since the checkpointer (not the process) is
what's holding the state. This is the mechanism `HumanInTheLoopMiddleware` (previewed in
Phase 1 Topic 08) wraps for `create_agent` users.

## Debugging

- `invoke()` raises instead of pausing cleanly → confirm the graph was compiled with a
  `checkpointer`; interrupts have nowhere to save state without one.
- Resuming re-runs an expensive step (like a paid API call) that happened *before* the
  `interrupt()` in the same node → move that call to its own earlier node so it isn't
  re-executed when the node restarts on resume.

## Mini challenge

Add a second `interrupt()` call in a different node (e.g. asking a human to edit the
draft's subject line before the approval step) and trace how two separate resumes are
needed to complete one run.
