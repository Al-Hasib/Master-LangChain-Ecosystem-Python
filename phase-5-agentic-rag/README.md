# Phase 5 — Agentic RAG

**Status:** 🗒️ Topic list only — ask for this phase by name to have it fully built out.

**The shift this phase teaches:** from "retrieve → answer" (fixed pipeline) to "agent
decides whether/how/what to retrieve" (retrieval as a tool call).

## Topics

01. **What is Agentic RAG?** — contrasting fixed-pipeline RAG (Phase 3–4) with agent-directed retrieval.
02. **Retriever as a Tool** — wrapping a vector store retriever as a LangChain tool an agent can call.
03. **Multi-Tool Retrieval: Web + SQL + Vector** — an agent choosing between multiple knowledge sources per query.
04. **Query Planning** — decomposing a complex question into sub-queries before retrieving.
05. **Retrieval & Answer Validation (Self-Corrective RAG)** — the agent checks its own retrieved context and answer, re-retrying on failure.
06. **Hybrid RAG & Project: AI Research Agent** — combining fixed-pipeline steps with agent-directed steps in one system.

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
