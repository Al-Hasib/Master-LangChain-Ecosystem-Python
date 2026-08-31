# 03 — Messages, Prompts & Prompt Templates

## Problem

Phase 0 built message lists as raw dicts (`{"role": "system", "content": ...}`). That
works for a script but not for a reusable application where the same prompt shape needs
different variables plugged in every call. LangChain gives messages a real type and
prompts a template mechanism for exactly this.

## Concept

**Message objects** (`langchain_core.messages`) — typed equivalents of Phase 0's dicts:
`SystemMessage`, `HumanMessage`, `AIMessage`, `ToolMessage`. Same roles, same
Phase-0-Topic-03 mental model, now with attributes instead of dict keys and proper
types the rest of LangChain (agents, streaming, LangGraph state) is built around.

**Prompt templates** (`ChatPromptTemplate`) — a prompt with placeholders, built once and
reused with different inputs:

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {persona} assistant."),
    ("human", "{question}"),
])
messages = prompt.invoke({"persona": "terse", "question": "What's a closure?"})
```

Templates are **composable with models** via LangChain Expression Language (`|`):

```python
chain = prompt | model
chain.invoke({"persona": "terse", "question": "What's a closure?"})
```

This `prompt | model` pattern (a "chain") is the fixed-workflow shape from Phase 0
Topic 07 — steps piped together in a fixed order, as opposed to an agent loop.

## Minimal code

`code.py` builds a `ChatPromptTemplate` with two variables, runs it through a `prompt | model` chain for three different variable sets, and separately builds the equivalent
message list by hand with typed message objects to show the two are interchangeable.

## Production notes

Prefer templates over f-string-formatted prompts once a prompt is reused in more than
one place — it keeps variable substitution explicit and (later, Phase 9) lets LangSmith
version and manage the prompt independently of your code.

## Debugging

- `KeyError` on `.invoke({...})` → a template variable name doesn't match what you
  passed; the error names the missing key.
- Model behaves inconsistently across "the same" prompt → check for accidental
  whitespace/formatting differences between template-generated and hand-built messages.

## Mini challenge

Add a `MessagesPlaceholder("history")` to the template so prior conversation turns can
be injected alongside the new templated system/human messages.
