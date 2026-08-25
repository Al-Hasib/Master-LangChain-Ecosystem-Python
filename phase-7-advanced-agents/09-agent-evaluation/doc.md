# 09 — Agent Evaluation

## Problem

Every topic in this phase has been "run it and eyeball the output." That doesn't scale
past a demo - you need a repeatable way to know whether a change to a prompt, a tool, or
a middleware made the agent *better* or *worse*, without re-reading transcripts by hand
every time.

## Concept

A minimal eval harness needs two kinds of checks, run over a fixed set of
`(question, expected_behavior)` test cases:

1. **Tool-call correctness** — a mechanical check: did the agent call the tool it was
   supposed to? This needs no LLM at all - just inspect
   `result["messages"]` for an `AIMessage` with the expected tool name in its
   `tool_calls`, the same trace-reading skill from Topic 01.
2. **Task success** — a judgment call: is the final answer actually good? Exact-string
   matching is too brittle for natural-language answers, so this uses **LLM-as-judge**:
   a separate structured-output call that takes the question, the agent's answer, and a
   description of what a correct answer looks like, and returns a `pass`/`fail` plus a
   reason.

```text
 test cases: [(question, expected_tool, expected_behavior), ...]
        │
        ▼
   run agent.invoke(question)  ──►  result["messages"]
        │                                  │
        ▼                                  ▼
 tool-call check                    LLM-as-judge check
 (mechanical: did it call           (structured output: passed, reason)
  expected_tool? yes/no)
        │                                  │
        └──────────────┬───────────────────┘
                        ▼
                 pass/fail summary
```

This is a manual, local harness - no LangSmith dataset/experiment tracking yet (that's
Phase 9 of the *course*, not to be confused with this being Topic 09 of *this* phase).
The point here is the *shape* of agent evaluation - mechanical checks plus a judged
check - which LangSmith later automates and records over time.

## Minimal code

`code.py` defines 4 test cases against a small agent (a calculator tool + a unit-
lookup tool), each with an `expected_tool` and a one-line `expected_behavior`
description. It runs every case, checks whether the expected tool was called, asks an
LLM judge whether the final answer satisfies the expected behavior, and prints a
pass/fail table plus an overall score.

## Production notes

Keep eval test cases small and fast-running (a handful, not hundreds) for a harness
you run on every change during development; reserve larger regression suites for CI.
An LLM judge is itself a model call with its own failure modes - keep its prompt
narrow (one specific judgment, not "is this good?") and periodically spot-check its
verdicts against your own judgment, the same way you'd spot-check any automated grader.

## Debugging

- Tool-call check always fails even though the agent clearly used the tool → you're
  checking `message.content` instead of `message.tool_calls` - the tool name lives in
  the latter.
- Judge is inconsistent across runs → set `temperature=0` on the judge model and make
  `expected_behavior` more specific (name the fact/value that must appear).
- Everything "passes" regardless of quality → your judge prompt is too lenient; ask it
  to justify a `False` explicitly by naming what's missing/wrong, not just rubber-stamp.

## Mini challenge

Add a 5th test case designed to fail (an `expected_behavior` the current agent can't
satisfy) and confirm the harness correctly reports it as a failure, not a false pass.
