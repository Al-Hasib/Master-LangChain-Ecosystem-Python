# 09 — Evaluation in CI/CD & Testing Agents

## Problem

Phase 9 covered running LangSmith evaluations interactively, by hand, when you suspect
something regressed. That catches problems *after* you notice them. A production app
needs the same kind of check to run automatically, on every change, *before* it ships —
otherwise "the agent stopped calling the right tool" is something a user reports, not
something CI caught.

## Concept

Treat agent behavior as testable, the same way you'd test any function with a fixed
input and an expected property of the output — the twist with an LLM-backed agent is
that you usually can't assert exact output text (it's non-deterministic), so you assert
a *property* instead: did it call the right tool, did it call it with roughly the right
arguments, did it avoid calling a tool it shouldn't have.

```text
fixed test case                 assertion (property, not exact text)
"What's 12 * 8?"          →     tool_calls contains "multiply" with a=12, b=8
"What's the weather       →     tool_calls contains "get_weather"
 in Paris?"
"Hello, how are you?"     →     tool_calls is EMPTY (shouldn't call a tool for chit-chat)
```

This repo's convention is standalone `python code.py` scripts, not a pytest suite
(consistent with every other topic in this course) — this topic keeps that convention:
`code.py` uses plain `assert` statements per case and prints a pass/fail summary, with a
nonzero exit code on failure. That summary and exit code are exactly what a CI job
needs (`python code.py; echo $?` — a real pipeline just runs this script as one step and
fails the build on a nonzero exit), so the same file works as a manual check and as a
CI gate without needing pytest as a new dependency for this course.

## Minimal code

`code.py` defines a small `create_agent(...)` with two tools (`multiply`, `get_weather`)
and three fixed test cases (two that should trigger a specific tool call, one that
shouldn't call any tool), asserts the expected property for each, and exits with status
1 if any case fails — printing a clear pass/fail table either way.

## Production notes

Wire this exact script (or its pytest equivalent, if a project already uses pytest
elsewhere) into CI as a required check before merge/deploy — a GitHub Actions step is
just `python 09-evaluation-in-cicd-and-testing-agents/code.py`. For the Phase project,
this is the gate that runs before Topic 10 ships a new container: broader coverage
(more cases, real LangSmith dataset evaluation per Phase 9) belongs in a scheduled or
pre-release job since it costs more and runs slower than this fast, fixed-case smoke
test suitable for every PR.

## Debugging

- A case fails intermittently → model non-determinism; pin `temperature=0` (already
  done here) and prefer asserting *which tool was called* over exact wording, which is
  what's actually stable across runs.
- A case fails after a prompt change but the behavior still looks "right" manually →
  the assertion may be too strict (e.g. checking exact argument order/formatting) —
  assert the semantic property (right tool, roughly right args), not incidental shape.
- CI passes locally but fails in the pipeline → check the pipeline actually has
  `OPENAI_API_KEY` set as a secret; these are real model calls, not mocked.

## Mini challenge

Add a fourth case that should trigger *both* tools in one turn (e.g. "What's 6 times 7,
and what's the weather in London?") and assert both tool calls happened, to test
multi-tool-call turns, not just single-tool ones.
