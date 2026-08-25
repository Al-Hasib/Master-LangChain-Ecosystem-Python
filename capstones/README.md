# Capstones — Portfolio-Grade Projects

**Status:** ✅ Fully built — every capstone has doc.md and code.py.

The course shouldn't end on a tutorial — it ends on projects a viewer can put in a
portfolio. Each capstone draws on multiple prior phases.

## [01 — Enterprise Knowledge Assistant (Production RAG)](01-enterprise-knowledge-assistant/doc.md)

Draws on: Phase 3–4 (RAG), Phase 9 (LangSmith), Phase 10 (production).

Features: PDF + web ingestion, hybrid retrieval, reranking, citations, conversation
memory, evaluation, full LangSmith tracing.

## [02 — Research Assistant (Agentic RAG)](02-agentic-research-assistant/doc.md)

Draws on: Phase 5 (agentic RAG), Phase 6 (LangGraph).

Features: web + vector search, query rewriting, retrieval grading, self-correction,
source citations, LangGraph orchestration.

## [03 — AI Business Analyst (Multi-Agent System)](03-ai-business-analyst/doc.md)

Draws on: Phase 6 (LangGraph), Phase 7 (advanced agents).

```text
                    Supervisor
          ┌─────────────┼─────────────┐
       Research       SQL Agent    Analyst
          └─────────────┼─────────────┘
                    Report Writer
                         ↓
                    Final Report
```

## [04 — Deep Research Agent](04-deep-research-agent/doc.md)

Draws on: Phase 8 (Deep Agents), Phase 9 (LangSmith).

Features: planning, subagents, web search, filesystem tools, context management, full
LangSmith instrumentation.
