# Phase 9 — LangSmith

**Status:** ✅ Fully built — every topic has doc.md and code.py.

**Treat this as a first-class phase, not an afterthought.** By this point in the course
viewers have several non-trivial apps (RAG, agents, multi-agent, deep agent) worth
making observable and evaluable.

## Topics

01. [What is LangSmith? & Project Setup](01-what-is-langsmith-and-project-setup/doc.md) — tracing, evaluation, prompts, deployment — the four pillars, and getting a project wired up.
02. [Tracing & Trace Hierarchy](02-tracing-and-trace-hierarchy/doc.md) — reading a trace tree for a chain/agent/graph run.
03. [Debugging Agents & Tool Calls](03-debugging-agents-and-tool-calls/doc.md) — using traces to find why an agent picked the wrong tool or looped.
04. [Prompt Management](04-prompt-management/doc.md) — versioning and iterating on prompts in LangSmith rather than in code.
05. [Datasets & Evaluators](05-datasets-and-evaluators/doc.md) — building a golden dataset, writing custom evaluators.
06. [LLM-as-a-Judge: RAG & Agent Evaluation](06-llm-as-a-judge-rag-and-agent-evaluation/doc.md) — automated grading of answer quality, groundedness, and agent task success.
07. [Experiments & Regression Testing](07-experiments-and-regression-testing/doc.md) — comparing prompt/model changes against a dataset over time.
08. [Monitoring & Production Observability](08-monitoring-and-production-observability/doc.md) — dashboards, alerts, and cost/latency tracking for a deployed app.

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
