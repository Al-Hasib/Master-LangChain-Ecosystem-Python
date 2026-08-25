# Phase 6 — LangGraph

**Status:** ✅ Fully built — every topic has doc.md and code.py.

**Don't introduce this too early.** The pitch for this phase is: "you've built LangChain
agents — now what if you need precise control over execution order, persistence, or a
human approval step?" That's exactly what LangGraph is for (the orchestration/runtime
layer under LangChain).

## Topics

01. [Why LangGraph? (LangChain vs LangGraph)](01-why-langgraph/doc.md) — when an agent loop isn't enough control.
02. [Graphs, Nodes, Edges & State](02-graphs-nodes-edges-and-state/doc.md) — the core mental model: state flows through nodes connected by edges.
03. [StateGraph & Conditional Edges](03-stategraph-and-conditional-edges/doc.md) — building a graph, branching execution on state.
04. [Checkpoints, Persistence & Threads](04-checkpoints-persistence-and-threads/doc.md) — durable execution; resuming a conversation/run across restarts.
05. [Streaming in LangGraph](05-streaming-in-langgraph/doc.md) — streaming intermediate node output, not just final tokens.
06. [Human-in-the-Loop & Interrupts](06-human-in-the-loop-and-interrupts/doc.md) — pausing a graph run for approval before a sensitive step.
07. [Time Travel & Error Handling](07-time-travel-and-error-handling/doc.md) — replaying/branching from a past checkpoint; retry strategies.
08. [Subgraphs & the Functional API](08-subgraphs-and-functional-api/doc.md) — composing graphs from graphs; the lighter-weight functional alternative to `StateGraph`.
09. [LangGraph Runtime & Production Architecture](09-langgraph-runtime-and-production-architecture/doc.md) — what changes going from local dev to a deployed graph.
10. [Project: Customer Support Workflow](10-project-customer-support-workflow/doc.md) — classify → route → agent → human approval → respond.
11. [Project: Agentic RAG with LangGraph](11-project-agentic-rag-with-langgraph/doc.md) — retriever tool + document grading + query rewriting + generation as an explicit graph (mirrors the official LangGraph agentic-RAG tutorial).

## Running the examples

```bash
pip install -r ../requirements.txt
cp ../.env.example ../.env   # fill in OPENAI_API_KEY at minimum
python 01-why-langgraph/code.py
```

## Phase projects

**Customer Support Workflow**

```text
User → Classify → [Billing | Technical | General] → Agent → Human Approval → Response
```

**Agentic RAG with LangGraph** — the Phase 5 agentic-RAG system rebuilt as an explicit,
inspectable graph with grading and rewrite loops.
