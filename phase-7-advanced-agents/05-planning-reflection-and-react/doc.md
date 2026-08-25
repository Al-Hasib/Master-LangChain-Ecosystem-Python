# 05 — Planning, Reflection & ReAct

## Problem

`create_agent`'s loop (Topic 01) is already a ReAct loop (Reason → Act → Observe,
repeat) - the model implicitly decides what to do next at every step. For simple
requests that's plenty. For a request with several moving parts, the model can start
executing before it's thought through the whole task, painting itself into a corner
(calling the wrong tool first, forgetting a sub-step). Two techniques help: make the
model **plan explicitly before acting**, and make it **critique its own draft answer**
before calling it done.

## Concept

- **Explicit planning** — before letting the agent loose with tools, ask the model for
  a short, structured plan (`list[str]` steps) via `with_structured_output` (Phase 1
  Topic 04's pattern). The plan is then fed back in as guidance for the tool-using
  agent. This trades one extra, cheap model call for a much lower chance of the agent
  wandering off-task on multi-part requests.
- **Reflection** — after the agent produces a draft final answer, make one more
  structured-output call asking the model to critique its own draft: is it correct and
  complete? If not, provide a revised answer. This is a self-check, not a second
  opinion from a different agent (that's Topic 08's job).

```text
 task
   │
   ▼
 planner (structured output: Plan.steps: list[str])
   │
   ▼
 create_agent loop, given the plan as guidance  ──►  draft answer
   │                                                        │
   │                                                        ▼
   │                                          reflector (structured output: Critique)
   │                                                        │
   │                       approved? ──yes──► draft answer is FINAL
   │                            │
   │                           no
   │                            ▼
   └──────────────────────► revised_answer is FINAL
```

Both steps reuse a technique you already have (`with_structured_output` +
Pydantic) - nothing new to learn, just a new place to apply it: around the agent loop
instead of only inside a tool.

## Minimal code

`code.py` gives a `calculate` tool (safe arithmetic only) and a multi-part word
problem. It first asks a `Plan` model for ordered steps, prints them, then runs
`create_agent` with the plan folded into the user message, then runs a `Critique`
model against the draft answer and prints whether it was approved or revised.

## Production notes

Planning pays off most on requests with 3+ distinct sub-tasks; for a single-tool
lookup it's pure overhead (an extra model call for no benefit) - gate it on request
complexity rather than always running it. Reflection catches arithmetic/logic slips the
first pass made but rarely catches an error the model is confidently, consistently
wrong about (self-critique inherits the same blind spots) - true error-catching needs
either a second, independently-prompted agent (Topic 08) or a deterministic check
(re-run the calculation and compare).

## Debugging

- Plan is ignored by the agent → make sure the plan text is actually inserted into
  what the agent sees (e.g. appended to the user message), not just printed for you.
- Reflection always approves → your critique prompt is too soft; ask it explicitly to
  look for a specific failure mode (e.g. "check the arithmetic step by step").
- Reflection always revises, even correct answers → the reflector's own uncertainty is
  driving false negatives; consider only revising when it names a *specific* error.

## Mini challenge

Add a `max_revisions` loop: if the reflector's revised answer is itself flagged as not
approved on a second pass, stop and return the best draft you have rather than looping
forever.
