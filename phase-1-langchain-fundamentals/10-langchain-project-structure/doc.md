# 10 — LangChain Project Structure

## Problem

Every topic so far has been one self-contained `code.py`. A real application has
multiple tools, possibly multiple agents, config, and needs to be testable — dumping it
all in one file stops working almost immediately.

## Concept

A structure that scales from "one agent" to "several agents + a RAG pipeline" without a
rewrite:

```text
my_app/
  config.py          # env vars / settings, loaded once, imported everywhere
  models.py           # init_chat_model(...) calls, one place to change providers
  tools/
    __init__.py        # exports the tool list
    search.py           # one file per logical tool group
    math_tools.py
  agents/
    research_agent.py   # create_agent(...) calls live here, not in main.py
  prompts/
    system_prompts.py   # ChatPromptTemplate / system prompt strings
  main.py              # entry point - wires config + tools + agent together, thin
tests/
  test_tools.py        # tools are plain functions - unit test them directly
```

Principles behind this layout:
- **Config lives in one place** (`config.py`), read from environment variables (never
  hardcoded keys) — this is what `.env` / `python-dotenv` are doing throughout this repo.
- **Tools are testable in isolation** — since `@tool`-decorated functions are still
  plain Python callables, they can be unit tested without invoking any model.
- **`main.py` stays thin** — it wires pieces together; logic lives in `tools/` and
  `agents/`.
- This repo's own layout (`phase-N/topic/code.py`) is a *teaching* layout, optimized for
  one-topic-per-file; a real app should use something closer to the structure above.

## Minimal code

`code.py` demonstrates the pattern in miniature within one file (since this is a
single-topic example): a `Settings` dataclass loaded from env vars, a small tools
module-level list, and a `main()` that only wires them together — comments mark where
each piece would move to its own file in a multi-file project.

## Production notes

Split into multiple files as soon as you have more than ~2-3 tools or more than one
agent — not before. Premature splitting has its own cost (navigating many tiny files).

## Debugging

Circular imports are the most common structural bug once you split `agents/` from
`tools/` — keep the dependency direction one-way: `agents` imports from `tools`, never
the reverse.

## Mini challenge

Take this topic's `code.py` and actually split it into the `config.py` / `tools/` /
`agents/` / `main.py` files sketched above, in a scratch folder.
