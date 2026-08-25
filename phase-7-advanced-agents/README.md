# Phase 7 — Advanced Agents

**Status:** ✅ Fully built — every topic has doc.md and code.py.

**This phase goes deep on agents** now that viewers know both LangChain (Phase 1) and
LangGraph (Phase 6) — single-agent sophistication first, then multi-agent systems.

## Topics

01. [Agent Architecture & Tool-Calling Agents](01-agent-architecture-and-tool-calling/doc.md) — recap and deepen the agent loop from Phase 1 with LangGraph-backed control.
02. [Agent Memory: Short-Term & Long-Term](02-agent-memory-short-term-and-long-term/doc.md) — conversation memory vs persisted cross-session memory.
03. [Context Management & Middleware](03-context-management-and-middleware/doc.md) — trimming/summarizing context, middleware hooks around the agent loop.
04. [Guardrails & Human-in-the-Loop Agents](04-guardrails-and-human-in-the-loop/doc.md) — input/output validation, approval gates for risky actions.
05. [Planning, Reflection & ReAct](05-planning-reflection-and-react/doc.md) — explicit plan-then-act loops; agents that critique their own output.
06. [Multi-Agent Systems Overview](06-multi-agent-systems-overview/doc.md) — why/when to split one agent into several.
07. [Supervisor, Router & Handoff Patterns](07-supervisor-router-and-handoff-patterns/doc.md) — the three standard multi-agent topologies.
08. [Parallel Agents & Collaboration](08-parallel-agents-and-collaboration/doc.md) — fan-out/fan-in agent execution.
09. [Agent Evaluation](09-agent-evaluation/doc.md) — measuring task success, tool-call correctness, and efficiency.

## Running the examples

```bash
pip install -r ../requirements.txt
cp ../.env.example ../.env   # fill in OPENAI_API_KEY at minimum
python 01-agent-architecture-and-tool-calling/code.py
```

## Phase project

**Multi-Agent Research System** — built out fully in
[Topic 07's supervisor example](07-supervisor-router-and-handoff-patterns/doc.md): a
supervisor agent coordinates four specialist agents (Research, Data, Analyst, Writer),
each exposed to it as a tool, to produce a final report.

```text
                 ┌── Research Agent
User → Supervisor├── Data Agent
                 ├── Analyst Agent
                 └── Writer Agent
                         ↓
                    Final Report
```
