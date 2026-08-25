# Phase 8 — Deep Agents

**Status:** 🗒️ Topic list only — ask for this phase by name to have it fully built out.

**Only introduce Deep Agents after LangChain + LangGraph** — viewers need the loop/graph
mental model to appreciate why a higher-level harness (planning, filesystem, subagents,
context management, all built in) is useful for long-running tasks.

## Topics

01. **What are Deep Agents?** — the problem class: long-horizon tasks a single tool-calling loop handles poorly.
02. **LangChain vs LangGraph vs Deep Agents** — where each layer sits and when to reach for which.
03. **Planning & Todo Lists** — the built-in planning tool that keeps a long task on track.
04. **Filesystem Tools & Context Management** — reading/writing scratch files instead of stuffing everything into context.
05. **Subagents & Delegation** — spinning up focused subagents for isolated sub-tasks.
06. **Long-Running Tasks & Deep Research Agents** — patterns for tasks that run far longer than one LLM call.
07. **Deep Agents + RAG / + LangGraph** — combining a deep agent with a retrieval backend or embedding it as a LangGraph node.
08. **When NOT to Use Deep Agents** — cases where a plain agent or explicit graph is the better, cheaper choice.

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
