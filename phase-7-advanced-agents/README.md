# Phase 7 — Advanced Agents

**Status:** 🗒️ Topic list only — ask for this phase by name to have it fully built out.

**This phase goes deep on agents** now that viewers know both LangChain (Phase 1) and
LangGraph (Phase 6) — single-agent sophistication first, then multi-agent systems.

## Topics

01. **Agent Architecture & Tool-Calling Agents** — recap and deepen the agent loop from Phase 1 with LangGraph-backed control.
02. **Agent Memory: Short-Term & Long-Term** — conversation memory vs persisted cross-session memory.
03. **Context Management & Middleware** — trimming/summarizing context, middleware hooks around the agent loop.
04. **Guardrails & Human-in-the-Loop Agents** — input/output validation, approval gates for risky actions.
05. **Planning, Reflection & ReAct** — explicit plan-then-act loops; agents that critique their own output.
06. **Multi-Agent Systems Overview** — why/when to split one agent into several.
07. **Supervisor, Router & Handoff Patterns** — the three standard multi-agent topologies.
08. **Parallel Agents & Collaboration** — fan-out/fan-in agent execution.
09. **Agent Evaluation** — measuring task success, tool-call correctness, and efficiency.

## Phase project

**Multi-Agent Research System**

```text
                 ┌── Research Agent
User → Supervisor├── Data Agent
                 ├── Analyst Agent
                 └── Writer Agent
                         ↓
                    Final Report
```
