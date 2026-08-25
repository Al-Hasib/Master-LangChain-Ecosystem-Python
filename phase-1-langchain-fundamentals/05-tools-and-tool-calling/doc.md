# 05 — Tools & Tool Calling

## Problem

Phase 0's tool was a manually-written JSON-schema dict describing a Python function.
Keeping that dict in sync with the function by hand doesn't scale past a couple of
tools. LangChain's `@tool` decorator generates the schema *from the function itself*.

## Concept

`@tool` turns a plain, well-documented Python function into something a model can be
offered and can request calls to:

```python
from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a named city."""
    ...
```

LangChain derives the tool's name, its parameter schema, and (from the docstring) its
description — the same three things Phase 0 wrote out by hand as a raw dict. Good
docstrings are not optional here: **the docstring is the only thing the model sees to
decide when to use the tool.**

`model.bind_tools([...])` offers a list of tools to a model for one call (what Topic 01
already used). A bound model's response has `.tool_calls` — zero or more requested
calls, each with a `name` and `args` you then execute yourself, exactly like Phase 0
Topic 04's round trip. `create_agent` (Topic 06) automates running that loop until the
model stops requesting tools.

## Minimal code

`code.py` defines three tools (`add`, `multiply`, `get_weather`) with `@tool`, binds all
three to a model, sends a question that requires two of them, and manually executes each
requested call — showing the multi-tool selection LangChain performs versus Phase 0's
single-tool example.

## Production notes

Write tool docstrings the way you'd write a short API doc for a coworker who's never
seen the function: what it does, when to use it, what each parameter means. Keep each
tool doing one thing — a model choosing between five overlapping tools performs worse
than choosing between five clearly distinct ones.

## Debugging

- Wrong tool called → docstrings overlap in scope; make them more specific /
  mutually exclusive.
- Tool never called → the docstring doesn't make it obvious the question needs it, or
  the question is ambiguous about needing a tool at all.
- `args` don't match the function signature → check type hints are present and correct;
  LangChain relies on them to build the parameter schema.

## Mini challenge

Add a fourth tool with a docstring deliberately overlapping `get_weather`'s scope (e.g.
"get_forecast") and see whether the model picks correctly or gets confused.
