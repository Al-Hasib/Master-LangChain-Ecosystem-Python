# 08 — When NOT to Use Deep Agents

## Problem

Every new tool in this course looks appealing right after you learn it — the real skill
is knowing when *not* to reach for it. Deep Agents adds real overhead (more bound tools
competing for the model's attention, more tokens spent on planning/filesystem calls, a
bigger, less predictable surface area) that isn't free.

## Concept

A short decision framework, in the spirit of Phase 2 Topic 07's vector-database chooser:

| Signal | Better fit |
|---|---|
| Task finishes in 1-3 tool calls | plain `create_agent` (Phase 1) |
| You need exact, auditable control over step order / branching | explicit LangGraph `StateGraph` (Phase 6) |
| You need a human-approval step at a specific point | LangGraph interrupts (Phase 6 Topic 06) — Deep Agents' `interrupt_on` exists but a plain graph gives more visible control |
| Latency/cost must be minimal and predictable | `create_agent` — every deep-agent add-on is extra tokens/tool-calls |
| The task is genuinely long-horizon (many phases, unpredictable step count, benefits from a persisted plan) | Deep Agents |
| Sub-work is noisy and needs isolating from the main context | Deep Agents (subagents) |

The common failure mode this topic warns about: reaching for `create_deep_agent` as a
default because it's "more capable" — the same trap as reaching for a distributed vector
database for a 500-document prototype (Phase 2 Topic 07). More machinery only pays off
once the task actually needs it (Topic 01's problem statement, restated as a warning).

## Minimal code

`code.py` is a small, pure-Python (no API key needed) scoring function — same shape as
Phase 2 Topic 07's vector-store chooser — that takes a few yes/no signals about a task
and recommends `create_agent`, explicit `LangGraph`, or `create_deep_agent`.

## Production notes

Re-evaluate this choice per-task, not per-project — a single application can reasonably
use plain `create_agent` for its fast-path chat and `create_deep_agent` for its "generate
a full report" feature, side by side.

## Debugging

If a `create_deep_agent` agent is calling `write_todos`/`task`/filesystem tools for
trivial single-step questions, that's a sign the task didn't need the harness — either
tighten the system prompt to discourage unnecessary planning, or drop back to
`create_agent` for that code path entirely.

## Mini challenge

Run the framework against three real tasks from earlier phases of this course (Phase 1
Topic 11's research assistant questions, for instance) and check whether it recommends
`create_agent` for all of them — it should, since none of those questions are genuinely
long-horizon.
