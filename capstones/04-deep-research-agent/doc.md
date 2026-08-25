# Capstone 04 — Deep Research Agent

## What this proves

Long-horizon research doesn't fit in one tool-calling loop: the task needs to be broken
into steps first, each step needs focused execution (not the whole conversation history
dragged along), and findings need to accumulate somewhere durable enough to survive
past any single LLM call's context window. That's the problem class Deep Agents (Phase
8) is built for. This capstone builds the same shape by hand: a planner that produces an
ordered list of steps (structured output), a delegation loop that hands each step to
either a focused web-research sub-agent or a note-taking step, an in-memory scratchpad
that stands in for a deep agent's filesystem tool, and a final synthesis pass that turns
the accumulated scratchpad into one structured report.

The portfolio-relevant skill: decomposing an open-ended research task into a concrete
plan, executing that plan step by step with isolated sub-agent calls instead of one
sprawling context, and synthesizing scattered findings into a single coherent
deliverable — the core loop behind every "deep research" product, built from first
principles.

## Draws on

- Phase 8 Topic 01 — What are Deep Agents? (the long-horizon-task problem class)
- Phase 8 Topic 03 — Planning & Todo Lists (the structured-output planner here)
- Phase 8 Topic 04 — Filesystem Tools & Context Management (the in-memory scratchpad
  stands in for this — see "What's simplified")
- Phase 8 Topic 05 — Subagents & Delegation (each plan step runs in its own focused
  sub-agent call, not the main conversation)
- Phase 1 Topic 04 — Structured output (plan + final report schemas)
- Phase 1 Topic 06 (`create_agent`) as the sub-agent primitive

## Architecture

```text
Research topic
      │
      ▼
Planner (structured output: ordered list of steps,     <- Phase 8 Topic 03
each step tagged web_search or note)
      │
      ▼
For each step, in order:
  ├── step_type == "web_search"
  │       │
  │       ▼
  │   Focused sub-agent (create_agent + web_search tool)   <- Phase 8 Topic 05
  │       │
  │       ▼
  │   finding appended to scratchpad (list[str])            <- Phase 8 Topic 04
  │       (stands in for a deep agent's filesystem tool)
  │
  └── step_type == "note"
          │
          ▼
      Summarize scratchpad-so-far into one note,
      appended back onto the scratchpad
      │
      ▼
Final synthesis (structured output: title, summary,
findings, sources, recommendation)                        <- built from full scratchpad
      │
      ▼
Structured Research Report
```

## Running it

```bash
cd capstones/04-deep-research-agent
python code.py
```

Requires `OPENAI_API_KEY` in `../.env`. Web search uses DuckDuckGo (no key required) and
is skipped gracefully per-step if there's no network access; the plan/scratchpad/
synthesis machinery needs no external files or services.

## What's simplified vs. a real production version

- **This does NOT use the real `deepagents` package.** Its API was independently
  verified against `docs.langchain.com/oss/python/deepagents/quickstart` during this
  capstone's build: `pip install deepagents`, then
  `from deepagents import create_deep_agent`, called as
  `create_deep_agent(model=..., tools=[...], system_prompt=...)`, which handles
  planning, filesystem tools, and subagent spawning automatically. That package isn't
  currently in this repo's `requirements.txt`, and this capstone's brief specifically
  calls for the hand-rolled plan-then-delegate version — so this implementation
  reproduces the *pattern* with `create_agent` + plain Python rather than adding a new
  dependency. Swapping in `create_deep_agent` directly is a natural extension once Phase
  8 is built out and the dependency is added deliberately.
- **The scratchpad is a plain Python `list[str]`**, not a real filesystem/virtual-files
  tool the agent can read/write/list on its own. It captures the "durable working
  memory across steps" idea without the actual tool-calling file interface.
- **The plan is fixed once generated** — no replanning mid-execution if a step's finding
  changes what later steps should look like (a real deep agent can update its own
  todo list as it works).
- **Each sub-agent call is stateless and isolated** (a fresh `create_agent` invocation
  per step) rather than a persistent subagent the planner can converse with further.

## Extend it further

- Add a replanning check after each step: if a finding contradicts an assumption in a
  later step, regenerate the remaining plan.
- Swap the `list[str]` scratchpad for actual read/write tools over a temp directory, as
  a closer stand-in for a deep agent's filesystem tool.
- Once Phase 8 is built and `deepagents` is deliberately added to `requirements.txt`,
  rebuild this exact capstone with `create_deep_agent` and compare line count, control,
  and output quality against this hand-rolled version.
