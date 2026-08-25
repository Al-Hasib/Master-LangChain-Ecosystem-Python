# 06 — Hybrid RAG & Project: AI Research Agent

## Problem

Every topic so far isolated one idea: agent-directed retrieval (01), a retriever tool
(02), multiple sources (03), planning (04), self-correction (05). A real system needs all
of them working together — and needs to know which parts should be a fixed, predictable
step and which parts should be left to the agent's judgment. This topic closes the phase
by building that system as the phase project.

## Concept

**Hybrid RAG** is the deliberate mix: some steps are a fixed workflow (Phase 0 Topic 07
sense) because they should *always* happen the same way; other steps are agent-directed
because the right action genuinely varies per question. Neither pure shape fits a real
research agent well — pure workflow can't adapt to arbitrary questions, pure agent
re-decides things (like "should I break this question apart?") that don't need
re-deciding every time.

```text
                                 FIXED step                    AGENT-DIRECTED step
                            (always the same way)             (model decides per sub-q)

User question ──► Query Planning (Topic 04) ──► sub-questions ──► Agent
                                                                    │
                                                        ┌───────────┼───────────┬───────────┐
                                                        ▼           ▼           ▼           ▼
                                                   Web Search  Vector Search   SQL         APIs
                                                        │           │           │           │
                                                        └───────────┴─────┬─────┴───────────┘
                                                                          ▼
                                                              Groundedness check (Topic 05)
                                                              -- retry once if not grounded --
                                                                          ▼
                                                                    Final Answer
```

This is the **AI Research Agent** — the project this whole phase and this repo's
"evolving project" narrative (root `README.md`) points to: Phase 1 Topic 11 built a
research assistant with fixed tools (calculator, web, date). Phase 5 gives it real
knowledge sources and the judgment to combine them: web search, vector search over its
own knowledge base, SQL over structured records, and a fourth **API** tool (any
external, non-DB, non-search data source — here, an exchange-rate lookup standing in for
a real REST API call).

## Minimal code

`code.py` wires up all four tools (`web_search`, `search_policies`, `query_orders_db`,
`get_exchange_rate`) on one `create_agent` agent, wraps it with the Topic 04 query-planning
step (always decompose first) and the Topic 05 groundedness check (validate the
synthesized answer; if ungrounded, run one more planning-and-answer pass), and runs it
end-to-end on a four-part compound question that needs every tool at least once.

## Production notes

This is still a teaching-scale build: in-code documents instead of a real ingestion
pipeline (Phase 2 Topic 08's connector), an in-memory SQLite table instead of a real
database, a hardcoded exchange-rate dict instead of a real API client. The *shape* —
fixed planning step, agent-directed tool selection, validation-with-retry — is exactly
what a production research agent uses; only the data sources change. LangGraph (Phase 6)
is where this shape gets rebuilt as an explicit, resumable graph instead of a script.

## Debugging

- Full pipeline is slow → count LLM round trips: planning (1) + agent-per-subquestion
  (1+ each) + synthesis (1) + groundedness (1) + possible retry (2+) adds up fast; this
  is the real cost of hybrid RAG and is worth surfacing on camera, not hiding.
- One sub-question's tool call fails silently and the synthesis just glosses over it →
  make tool functions return an explicit `"Error: ..."` string on failure (never an
  empty string) so the synthesis step has something to react to instead of nothing.

## Mini challenge

Swap the always-run query-planning step for a conditional one (only decompose if the
question contains more than one "?" or the word "and" more than once) and compare total
LLM calls on a simple, single-part question before and after — this is the gating
strategy Topic 04's production notes pointed at, now applied to the full project.
