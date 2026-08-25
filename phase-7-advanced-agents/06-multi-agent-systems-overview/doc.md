# 06 — Multi-Agent Systems Overview

## Problem

Topics 01-05 made **one** agent more sophisticated: memory, guardrails, planning,
reflection. But a single agent with one system prompt and one tool list eventually
hits a ceiling - too many tools confuse tool selection, one prompt trying to be good at
research *and* writing *and* data analysis is mediocre at all three, and everything
runs sequentially even when parts of the work don't depend on each other.

## Concept

**Multi-agent systems** split one monolithic agent into several smaller, specialized
agents that collaborate. The motivation is almost always one (or more) of:

- **Separation of concerns** — a "research" agent and a "writer" agent each get a
  focused system prompt and a small, relevant tool list, instead of one agent juggling
  both jobs (and both sets of tools) at once.
- **Specialization** — a narrower prompt + tool list measurably improves tool-selection
  accuracy and output quality versus one agent trying to do everything.
- **Parallelizable work** — independent sub-tasks (Topic 08) can run concurrently
  instead of one agent doing them one after another.

This isn't free: more agents means more orchestration code, more LLM calls (cost/
latency), and a new failure mode - agents miscommunicating at the handoff. Reach for
multi-agent only once a single, well-built agent (Topics 01-05's techniques) actually
hits its ceiling.

```text
  ONE agent, growing prompt + tool list          SEVERAL agents, focused each
  ┌─────────────────────────────────┐            ┌──────────┐    ┌──────────┐
  │ "research AND analyze AND write"│     -->     │ research │───▶│  writer  │
  │  tools: [search, calc, format,  │            │  agent   │    │  agent   │
  │          ...12 more]             │            └──────────┘    └──────────┘
  └─────────────────────────────────┘             (each: focused prompt, few tools)
```

The three standard ways agents hand work to each other - **router**, **supervisor**,
and explicit **handoff** - are covered fully with runnable code in Topic 07. This topic's
code is the smallest possible version of that idea: two agents, one explicit handoff.

Multi-agent systems can be hand-rolled with plain Python (as this phase does - a
routing function or a tool-wrapped sub-agent call) or built as an explicit LangGraph
graph with agent nodes (Phase 6) when you need shared persisted state, checkpointing,
or visual/debuggable control flow across agents.

## Minimal code

`code.py` builds a `research_agent` (has a fake search tool, gathers raw facts) and a
`writer_agent` (no tools, just turns raw facts into a polished answer). The research
agent's output is explicitly handed off - passed as the writer agent's input message -
proving the two agents share no state or tools, only the text passed between them.

## Production notes

Start with the smallest number of agents that solves the specialization/separation
problem you actually have - two is often enough. Log the handoff payload (what exactly
agent A passed to agent B) the same way you'd log a function's return value; it's the
one place multi-agent systems fail silently.

## Debugging

- Writer agent's output ignores the research agent's findings → check the handoff
  message actually contains the research output, not just a generic pointer to it (e.g.
  "see above" means nothing to an agent with a fresh message list).
- Nothing seems to run in parallel → sequential handoff (this topic) is inherently
  sequential by design; for real concurrency see Topic 08.

## Mini challenge

Add a third agent, `fact_checker_agent`, that reviews the research agent's findings
before handing off to the writer agent - a three-agent sequential pipeline.
