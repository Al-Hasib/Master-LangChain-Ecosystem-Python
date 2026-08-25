# Phase 9 — LangSmith

**Status:** 🗒️ Topic list only — ask for this phase by name to have it fully built out.

**Treat this as a first-class phase, not an afterthought.** By this point in the course
viewers have several non-trivial apps (RAG, agents, multi-agent, deep agent) worth
making observable and evaluable.

## Topics

01. **What is LangSmith? & Project Setup** — tracing, evaluation, prompts, deployment — the four pillars, and getting a project wired up.
02. **Tracing & Trace Hierarchy** — reading a trace tree for a chain/agent/graph run.
03. **Debugging Agents & Tool Calls** — using traces to find why an agent picked the wrong tool or looped.
04. **Prompt Management** — versioning and iterating on prompts in LangSmith rather than in code.
05. **Datasets & Evaluators** — building a golden dataset, writing custom evaluators.
06. **LLM-as-a-Judge: RAG & Agent Evaluation** — automated grading of answer quality, groundedness, and agent task success.
07. **Experiments & Regression Testing** — comparing prompt/model changes against a dataset over time.
08. **Monitoring & Production Observability** — dashboards, alerts, and cost/latency tracking for a deployed app.

## Phase project

Take the **RAG Agent** from Phase 5 and instrument it end-to-end:

```text
User → Application → LangChain/LangGraph → LangSmith
                        ├── Traces
                        ├── Evaluation
                        ├── Datasets
                        ├── Monitoring
                        └── Debugging
```
