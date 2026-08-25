# Capstone 02 — Agentic Research Assistant (Agentic RAG)

## What this proves

Capstone 01 always retrieves. This one proves the Phase 5 shift: retrieval becomes a
**decision**, not a fixed step. One agent is handed two knowledge sources — a vector
store of internal docs and live web search — and has to pick the right one per
question, notice when its first attempt came back weak, rewrite the query, and try
again before answering. That loop (retrieve → judge → rewrite → retrieve again) is the
core mechanic behind every "agentic RAG" and self-corrective RAG system, kept here as
a small, inspectable, hand-rolled flow rather than a black box.

The portfolio-relevant skill: showing an agent make *and justify* a retrieval-source
decision, and recover from a bad first attempt instead of confidently answering off
weak context — the two failure modes that make naive single-shot RAG unreliable.

## Draws on

- Phase 5 Topic 01 — What is Agentic RAG? (agent-directed retrieval vs. fixed pipeline)
- Phase 5 Topic 02 — Retriever as a Tool (vector store wrapped as a `@tool`)
- Phase 5 Topic 03 — Multi-Tool Retrieval: Web + SQL + Vector (here: web + vector)
- Phase 5 Topic 04 — Query Planning (query rewriting when retrieval looks weak)
- Phase 5 Topic 05 — Retrieval & Answer Validation (Self-Corrective RAG)
- Phase 6's core idea — explicit, inspectable control flow over a single opaque agent
  loop — applied here in hand-rolled Python rather than a real `StateGraph`, since
  Phase 6 is being built independently and its exact API isn't assumed here (see
  "What's simplified")
- Phase 1 Topic 06 (`create_agent`) and Topic 05 (`@tool`) as the underlying primitives

## Architecture

```text
User question
      │
      ▼
create_agent(tools=[vector_search, web_search])   <- Phase 1 Topic 06, Phase 5 Topic 02/03
      │  (agent decides which tool, or both, to call)
      ▼
Tool result(s)
      │
      ▼
weak_result? ──no──► Answer with citations
      │
     yes                                          <- Phase 5 Topic 05 (self-check)
      ▼
Query rewrite (structured output)                 <- Phase 5 Topic 04
      │
      ▼
Re-invoke agent with rewritten query
      │
      ▼
Answer with citations (best available context, labeled if still weak)
```

## Running it

```bash
cd capstones/02-agentic-research-assistant
python code.py
```

Requires `OPENAI_API_KEY` in `../.env`. Web search uses DuckDuckGo (no key required,
same pattern as Phase 1 Topic 11) and is wrapped in try/except so the script still runs
(with a printed skip notice) if there's no network access; the vector-search path needs
no network at all.

## What's simplified vs. a real production version

- **The retrieve → judge → rewrite loop is hand-rolled Python, not a real LangGraph
  graph with conditional edges and cycles.** Phase 6 is being built concurrently in this
  repo and its exact `StateGraph`/conditional-edge API isn't depended on here — this
  capstone proves the *pattern* (self-correction via an explicit loop) without assuming
  an unverified import path. Rebuilding this exact flow as a LangGraph graph is Phase
  6's own project.
- **The "weak result" check is a heuristic** (empty/very short tool output, or an
  explicit "no results" string), not a learned or LLM-graded relevance score like
  Capstone 01's grader — good enough to demonstrate the retry mechanic, not a tuned
  production heuristic.
- **The query rewrite happens at most once.** A production self-corrective loop might
  retry multiple times with a budget/backoff; one retry is enough to prove the mechanic.
- **The in-code vector corpus is small** (10 short internal-engineering documents) for
  the same standalone-runnability reason as Capstone 01.

## Extend it further

- Add a third tool (SQL, as in Capstone 03) and let the agent choose across three
  sources instead of two.
- Replace the heuristic "weak result" check with Capstone 01's LLM-based relevance
  grader for a more robust self-correction trigger.
- Once Phase 6 is built out, rebuild this exact flow as a real `StateGraph` with a
  conditional edge on the "weak result" check, and compare the two implementations
  side by side.
