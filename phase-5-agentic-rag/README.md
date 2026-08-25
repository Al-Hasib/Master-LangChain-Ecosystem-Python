# Phase 5 — Agentic RAG

**Status:** ✅ Fully built — every topic has doc.md and code.py.

**The shift this phase teaches:** from "retrieve → answer" (fixed pipeline) to "agent
decides whether/how/what to retrieve" (retrieval as a tool call).

## Topics

01. [What is Agentic RAG?](01-what-is-agentic-rag/doc.md) — contrasting fixed-pipeline RAG (Phase 3–4) with agent-directed retrieval.
02. [Retriever as a Tool](02-retriever-as-a-tool/doc.md) — wrapping a vector store retriever as a LangChain tool an agent can call.
03. [Multi-Tool Retrieval: Web + SQL + Vector](03-multi-tool-retrieval-web-sql-vector/doc.md) — an agent choosing between multiple knowledge sources per query.
04. [Query Planning](04-query-planning/doc.md) — decomposing a complex question into sub-queries before retrieving.
05. [Retrieval & Answer Validation (Self-Corrective RAG)](05-retrieval-and-answer-validation-self-corrective-rag/doc.md) — the agent checks its own retrieved context and answer, re-retrying on failure.
06. [Hybrid RAG & Project: AI Research Agent](06-hybrid-rag-and-project-ai-research-agent/doc.md) — combining fixed-pipeline steps with agent-directed steps in one system.

## Phase project

**AI Research Agent** — one agent with web search, vector search, SQL, and API tools
that decides which to use per question.

```text
                    ┌── Web Search
User → Agent ───────┼── Vector Search
                    ├── SQL
                    └── APIs
                         ↓
                    Final Answer
```
