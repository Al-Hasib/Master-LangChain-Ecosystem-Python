# 02 — Retriever as a Tool

## Problem

Topic 01 wrapped a retriever in a hand-written `@tool` function. That works, but it's
boilerplate you'd rewrite for every retriever in every project: call `.invoke()`, join
the results, return a string. LangChain ships a helper that does exactly this,
consistently, so you write it once and move on.

## Concept

`create_retriever_tool` turns any `BaseRetriever` (what `vectorstore.as_retriever()`
returns — Phase 3 Topic 05) into a ready-to-use LangChain tool: give it the retriever, a
`name`, and a `description`, and it produces a tool that formats retrieved documents
into a string the model can read, the same shape Topic 01's hand-written version
produced by hand.

```python
from langchain_core.tools.retriever import create_retriever_tool

retriever_tool = create_retriever_tool(
    retriever,
    name="search_policies",
    description="Search Aurora's internal policy docs. Only for Aurora-specific "
    "questions - not general knowledge.",
)
```

Verified against the current LangChain reference docs: `create_retriever_tool` lives in
`langchain_core.tools.retriever` (it's also re-exported from `langchain_core.tools` for
convenience). It returns a `StructuredTool`, so it plugs into `create_agent`'s `tools=`
list exactly like any `@tool`-decorated function — the agent can't tell the difference.

```text
vectorstore.as_retriever()  ->  BaseRetriever
                                     │
                     create_retriever_tool(retriever, name, description)
                                     │
                                     ▼
                              StructuredTool  ──────►  create_agent(tools=[...])
```

The `description` matters more here than for most tools: it is the *only* signal the
model has for deciding whether a question needs this particular knowledge base versus
being answered directly or with a different tool (Topic 03 adds more).

## Minimal code

`code.py` builds a Chroma retriever over the same Aurora knowledge base as Topic 01,
wraps it with `create_retriever_tool` in one line, and gives an agent *only* that tool.
It asks one on-topic question and one off-topic question (a plain greeting) to show the
agent calling the tool only when relevant — exactly Topic 01's behavior, with less code.

## Production notes

Write the `description` the way you'd write documentation for a teammate who has never
seen your data: name the domain it covers ("Aurora's billing and support policies") and,
just as importantly, what it *doesn't* cover. Vague descriptions ("search documents")
cause both false positives (called when irrelevant) and false negatives (skipped when
needed).

## Debugging

- `ImportError` on `langchain_core.tools.retriever` → you're on an old LangChain
  version; the fallback is a plain `@tool` wrapping `retriever.invoke(query)` (Topic
  01's pattern) — functionally identical, just more typing.
- Tool called but agent's answer ignores the results → check `document_separator`/what
  the retriever actually returns; an empty or near-empty top-k gives the model nothing
  to ground an answer in.

## Mini challenge

Swap `create_retriever_tool`'s `name` and `description` for something vague ("tool1",
"searches stuff") and rerun both questions — observe the agent's tool-call decisions get
noticeably less reliable, proving the description is doing real work, not just cosmetic.
