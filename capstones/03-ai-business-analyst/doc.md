# Capstone 03 — AI Business Analyst (Multi-Agent System)

## What this proves

One agent with a pile of tools starts to strain once a task needs genuinely different
*kinds* of work — pulling external context, querying structured data, and reasoning
over both together. This capstone splits that work across specialized sub-agents
coordinated by a supervisor, the standard multi-agent topology (Phase 7 Topic 07):
route → gather in parallel-ish stages → synthesize → write. It's the same idea a real
team uses when it splits "research," "data," and "writing" across different people
instead of asking one generalist to do everything serially.

The portfolio-relevant skill: designing a multi-agent system's *control flow* by hand —
deciding what each sub-agent owns, what shape its output takes, and how a supervisor
combines heterogeneous results (free text from research, rows from SQL, structured
analysis) into one coherent report — without leaning on a framework's opinions about
how that routing should work.

## Draws on

- Phase 7 Topic 06 — Multi-Agent Systems Overview (why/when to split one agent into several)
- Phase 7 Topic 07 — Supervisor, Router & Handoff Patterns
- Phase 7 Topic 01 — Agent Architecture & Tool-Calling Agents (each sub-agent is a
  `create_agent` instance)
- Phase 1 Topic 04 — Structured output (the Analyst sub-agent's findings)
- Phase 2 Topic 04's SQL-to-`Document` pattern, adapted here to direct SQL querying via
  an agent tool instead of a document-loading step
- Phase 5 Topic 03 — Multi-Tool Retrieval: Web + SQL + Vector (the underlying idea that
  different sub-agents/tools serve different data sources)

## Architecture

```text
                    Supervisor                         <- Phase 7 Topic 07
          ┌─────────────┼─────────────┐
     Research Agent   SQL Agent    (both feed into)
     (web_search)     (run_sql on
                       in-memory
                       sales table)
          └─────────────┼─────────────┘
                         ▼
                   Analyst Agent                        <- structured output
              (key metrics / trends / risks /
                    recommendation)
                         ▼
                  Report Writer                          <- plain LLM synthesis
                         ▼
                   Final Report
```

Routing is plain Python, not a framework: `supervisor_plan()` uses structured output to
decide which of Research/SQL are actually needed for a given business question, then the
script calls each selected sub-agent as an ordinary function and threads results forward
— no dependency on an unverified multi-agent framework API.

## Running it

```bash
cd capstones/03-ai-business-analyst
python code.py
```

Requires `OPENAI_API_KEY` in `../.env`. The "sales database" is an in-memory SQLite
table populated with fake data at startup — no external database or files needed. Web
search uses DuckDuckGo and is skipped gracefully (with a printed notice) if offline.

## What's simplified vs. a real production version

- **Routing is hand-rolled Python function calls, not a real supervisor graph.** A
  production multi-agent system (e.g. built on Phase 6 LangGraph once it exists, or a
  vetted supervisor package) would model this as an actual graph with retries, partial
  failure handling, and parallel execution. Here, sub-agents run sequentially and the
  "supervisor" is one structured-output call plus an if/else — proving the *pattern*
  without depending on an unverified multi-agent framework import, per this course's
  house rule of never guessing at APIs.
- **The SQL agent's `run_sql` tool executes arbitrary SQL against an in-memory,
  throwaway SQLite database** with no write protection beyond the fact that the schema
  is recreated every run. A production system would use a read-only DB role and a
  query-validation layer before ever letting an LLM-generated query run.
- **No inter-agent negotiation or replanning** — the supervisor decides once, upfront,
  which sub-agents to run; it doesn't re-route based on a sub-agent's output the way a
  more sophisticated planner might.
- **The fake sales dataset is small** (~20 rows across 2 quarters) purely so the SQL
  agent's queries stay fast and legible on screen.

## Extend it further

- Add a fourth sub-agent (e.g. "Competitor Watcher") and give the supervisor a real
  decision to make about whether it's relevant to a given question.
- Make the Analyst agent's structured output drive a conditional second pass — if
  `risks` is non-empty, route back to the Research agent for follow-up before the
  Report Writer runs.
- Swap the hand-rolled routing for a real LangGraph graph once Phase 6 is built out, and
  compare readability/observability between the two approaches.
