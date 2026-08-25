# 03 — Multi-Tool Retrieval: Web + SQL + Vector

## Problem

Real systems rarely have one knowledge source. Aurora Cloud Analytics' policies live in
a vector store (Topic 02), its order history lives in a relational database, and general
questions ("what is LangGraph?") need the open web — none of which any single retriever
covers. Fixed-pipeline RAG can only query one source per step; an agent can pick.

## Concept

Give one agent three tools, each wrapping a different retrieval mechanism, and let the
model's tool-selection (Phase 1 Topic 05) decide which source(s) a question needs:

```text
                    ┌── search_policies   (vector store  - Topic 02's create_retriever_tool)
User -> Agent ──────┼── query_orders_db   (SQL           - sqlite, SELECT-only)
                    └── web_search        (web           - DuckDuckGo, Phase 1 Topic 11's pattern)
```

Each tool's **description is the routing logic** — there's no `if/elif` dispatcher in
your code (Phase 0 Topic 01 called that out for tool calling in general; here it applies
to *retrieval sources specifically*). The SQL tool takes a raw `SELECT` statement rather
than a natural-language question, so the model has to translate the question into SQL
itself — the same skill Phase 2's SQL loader topic touched on, now agent-driven instead
of hand-written.

## Minimal code

`code.py` wires up all three tools on one `create_agent` agent and asks four questions:
one that clearly needs only the vector store, one that clearly needs only SQL, one that
clearly needs only the web, and one that needs **both** SQL and the vector store (an
order's status, plus what the return policy says about it). The full message trace shows
exactly which tool(s) fired per question.

## Production notes

Guard the SQL tool: never let a model-generated string execute unrestricted SQL against
a real database. `code.py` allows only statements that start with `SELECT` as a minimal
example — a production system would use a read-only DB role/connection as the real
safety boundary, with the string check as a cheap first line of defense, not the only
one.

## Debugging

- Agent queries SQL with an invalid column/table name → give the tool's docstring the
  exact schema (table + column names) instead of assuming the model can guess it;
  schema-in-the-description is doing the same job Topic 02's description did for scope.
- Agent picks only one tool for the two-source question → make sure the system prompt
  says tools can be combined ("call as many tools as needed before answering"), since
  some models default to stopping after the first successful call.

## Mini challenge

Add a question that needs all three sources in one answer (e.g. "What's LangGraph, is it
mentioned in Aurora's docs, and does customer Maria Lopez have an active order?") and see
whether the agent chains all three tool calls before producing one synthesized answer.
