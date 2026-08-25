# Phase 8 — Deep Agents

**Status:** ✅ Fully built — every topic has doc.md and code.py.

**Only introduce Deep Agents after LangChain + LangGraph** — viewers need the loop/graph
mental model to appreciate why a higher-level harness (planning, filesystem, subagents,
context management, all built in) is useful for long-running tasks.

## Topics

01. [What are Deep Agents?](01-what-are-deep-agents/doc.md) — the problem class: long-horizon tasks a single tool-calling loop handles poorly.
02. [LangChain vs LangGraph vs Deep Agents](02-langchain-vs-langgraph-vs-deep-agents/doc.md) — where each layer sits and when to reach for which.
03. [Planning & Todo Lists](03-planning-and-todo-lists/doc.md) — the built-in planning tool that keeps a long task on track.
04. [Filesystem Tools & Context Management](04-filesystem-tools-and-context-management/doc.md) — reading/writing scratch files instead of stuffing everything into context.
05. [Subagents & Delegation](05-subagents-and-delegation/doc.md) — spinning up focused subagents for isolated sub-tasks.
06. [Long-Running Tasks & Deep Research Agents](06-long-running-tasks-and-deep-research-agents/doc.md) — patterns for tasks that run far longer than one LLM call.
07. [Deep Agents + RAG / + LangGraph](07-deep-agents-plus-rag-plus-langgraph/doc.md) — combining a deep agent with a retrieval backend or embedding it as a LangGraph node.
08. [When NOT to Use Deep Agents](08-when-not-to-use-deep-agents/doc.md) — cases where a plain agent or explicit graph is the better, cheaper choice.

## Phase project

**Deep Research Agent**

```text
User → Deep Agent → Planner
         ├── Research Subagent
         ├── Web Search
         ├── Document Research
         ├── Data Analysis
         └── Fact Checking
              ↓
        Context Management
              ↓
         Final Report
```
