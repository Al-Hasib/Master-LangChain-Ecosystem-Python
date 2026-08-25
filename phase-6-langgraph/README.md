# Phase 6 — LangGraph

**Status:** 🗒️ Topic list only — ask for this phase by name to have it fully built out.

**Don't introduce this too early.** The pitch for this phase is: "you've built LangChain
agents — now what if you need precise control over execution order, persistence, or a
human approval step?" That's exactly what LangGraph is for (the orchestration/runtime
layer under LangChain).

## Topics

01. **Why LangGraph? (LangChain vs LangGraph)** — when an agent loop isn't enough control.
02. **Graphs, Nodes, Edges & State** — the core mental model: state flows through nodes connected by edges.
03. **StateGraph & Conditional Edges** — building a graph, branching execution on state.
04. **Checkpoints, Persistence & Threads** — durable execution; resuming a conversation/run across restarts.
05. **Streaming in LangGraph** — streaming intermediate node output, not just final tokens.
06. **Human-in-the-Loop & Interrupts** — pausing a graph run for approval before a sensitive step.
07. **Time Travel & Error Handling** — replaying/branching from a past checkpoint; retry strategies.
08. **Subgraphs & the Functional API** — composing graphs from graphs; the lighter-weight functional alternative to `StateGraph`.
09. **LangGraph Runtime & Production Architecture** — what changes going from local dev to a deployed graph.
10. **Project: Customer Support Workflow** — classify → route → agent → human approval → respond.
11. **Project: Agentic RAG with LangGraph** — retriever tool + document grading + query rewriting + generation as an explicit graph (mirrors the official LangGraph agentic-RAG tutorial).

## Phase projects

**Customer Support Workflow**

```text
User → Classify → [Billing | Technical | General] → Agent → Human Approval → Response
```

**Agentic RAG with LangGraph** — the Phase 5 agentic-RAG system rebuilt as an explicit,
inspectable graph with grading and rewrite loops.
