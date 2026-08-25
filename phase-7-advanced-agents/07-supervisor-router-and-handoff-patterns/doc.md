# 07 — Supervisor, Router & Handoff Patterns

## Problem

Topic 06 established *why* to split one agent into several. This topic covers *how* -
the three standard topologies for wiring multiple agents together, each suited to a
different shape of problem.

## Concept

- **Router** — classify the request once, then dispatch to exactly one of several
  specialist agents. Cheap, predictable, good when requests fall into clear, disjoint
  categories (billing vs. technical support).
- **Supervisor** — one coordinating agent that treats other agents **as tools**. The
  supervisor decides which specialist(s) to call, in what order, possibly more than
  once, and composes their outputs into a final result. Good for multi-step work where
  the coordinator itself needs to reason about sequencing.
- **Handoff** — an agent, mid-conversation, recognizes it can't (or shouldn't) continue
  and explicitly transfers control to another agent, which picks up from there. Good
  for triage-style flows where the first agent's real job is knowing when *not* to
  answer.

```text
ROUTER                    SUPERVISOR                     HANDOFF
                                                    (agent A working...)
 request                  request                        │
   │                        │                        "not my job"
   ▼                        ▼                             │
classify              supervisor agent                    ▼
   │                    (calls agents AS TOOLS)      agent B takes over
 ┌─┴─┐                   ┌────┬────┬────┐             from A's context
 ▼   ▼                   ▼    ▼    ▼    ▼
 A   B                research data analyst writer
(exactly one)         (any subset, any order, decided by the supervisor's own reasoning)
```

The supervisor pattern is what production "multi-agent" usually means: an
LLM-as-orchestrator, using ordinary tool-calling (Topic 01) where each "tool" happens to
be `sub_agent.invoke(...)` wrapped in a `@tool` function instead of a plain Python
function. No special framework is required - `create_agent` + `@tool` is enough, which
is why this repo hand-rolls it rather than depending on an unverified third-party
supervisor package.

## Minimal code

`code.py` has three sections:

- **(a) Router** — classifies a request as `billing` or `technical` via structured
  output, dispatches to one of two specialist agents.
- **(b) Supervisor — the Phase 7 project (Multi-Agent Research System)** — a
  `supervisor` agent with four tools, each wrapping a specialist agent's `.invoke()`:
  `research_tool` (facts), `data_tool` (numbers), `analyst_tool` (synthesis),
  `writer_tool` (final prose). The supervisor decides the call order itself and returns
  the writer's report as the final answer - this is the real phase capstone, not a toy.
- **(c) Handoff** — a `general_agent` that, on recognizing a billing question, calls a
  `handoff_to_billing` tool instead of answering; the orchestrating code detects that
  tool call and explicitly invokes `billing_agent` with the handed-off summary.

```text
                 ┌── Research Agent (research_tool)
User → Supervisor├── Data Agent      (data_tool)
                 ├── Analyst Agent   (analyst_tool)
                 └── Writer Agent    (writer_tool)
                         ↓
                    Final Report
```

## Production notes

Router is the cheapest and most predictable - prefer it when categories are genuinely
disjoint. Supervisor costs more (the coordinator is itself a full agent loop on top of
each specialist's loop) but handles work that doesn't decompose into a fixed sequence.
Handoff is the right shape for triage/escalation flows (support bots, sales-to-support
transfer) where losing the original conversation context on transfer would be a real
regression - always pass a summary or the full message history, never just "the user
has a billing question" with no detail.

## Debugging

- Supervisor calls specialist tools in a strange order or skips one → tighten the
  supervisor's `system_prompt` with the exact expected sequence, the same way a vague
  tool docstring causes misordered calls (Topic 01).
- Router misclassifies → structured-output classification is only as good as the
  category descriptions; add a short example per category to the classification prompt.
- Handoff "loses" context → confirm you're passing the handoff tool's actual argument
  (the summary) into the receiving agent's input, not a generic placeholder.

## Mini challenge

Add a fifth specialist, `fact_checker_tool`, to the supervisor's toolbox and update its
system prompt so it's called after `research_tool` but before `analyst_tool`.
