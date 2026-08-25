# 01 — What is LangSmith? & Project Setup

## Problem

Every phase since Phase 1 has told you to inspect `result["messages"]` or add a `print()`
when something goes wrong (Phase 1 Topic 06's production notes literally say that's your
"first debugging tool before reaching for LangSmith"). That works for a five-line script.
It stops working the moment you have a multi-step chain, an agent that loops, a
retriever, and a fallback (Phase 1 Topic 08) all nested inside one call — you can't
`print()` your way through a call tree three or four levels deep, across many runs, over
time, in production.

LangSmith is the answer to "I can't see what my LangChain/LangGraph app actually did."

## Concept

LangSmith is **not a new application shape** — nothing you built in Phases 1–8 changes.
It's an observability/evaluation layer you turn on around existing code, built on four
pillars:

```text
┌─────────────────────────────────────────────────────────────────┐
│                          LANGSMITH                                │
├───────────────┬───────────────┬───────────────┬──────────────────┤
│   TRACING      │  EVALUATION   │    PROMPTS     │    DEPLOYMENT     │
│  (Topics 2-3)  │ (Topics 5-7)  │   (Topic 4)    │    (Topic 8)      │
│                │               │                │                   │
│ see every step │ score outputs │ version/share  │ monitor a live    │
│ of a run, incl.│ against a     │ prompts outside│ deployment: cost, │
│ nested calls   │ dataset,      │ of code, LLM-  │ latency, error    │
│                │ automatically │ judge or human │ rate over time    │
└───────────────┴───────────────┴───────────────┴──────────────────┘
```

Turning tracing on is three environment variables — no wrapper classes, no changed
function signatures:

```text
LANGCHAIN_TRACING_V2=true   # "start sending traces"
LANGCHAIN_API_KEY=...       # "who's sending them" (from smith.langchain.com)
LANGCHAIN_PROJECT=...       # "which project/dashboard they land in"
```

**A naming note, because it trips people up:** LangSmith's current docs write these as
`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`. Both spellings are real —
the `langsmith` SDK looks for either prefix (checking `LANGSMITH_*` first, falling back
to `LANGCHAIN_*`), so the `LANGCHAIN_*` names already sitting in this repo's
`.env.example` are not stale, just the older/still-fully-supported spelling. This course
keeps using `LANGCHAIN_*` for consistency with `.env.example`; mentally substitute
`LANGSMITH_*` if you're copying commands from LangSmith's own docs site.

Once those variables are set, **every LangChain/LangGraph construct traces itself
automatically** — `init_chat_model`, `create_agent`, retrievers, chains built with `|`.
You don't call anything to "start a trace"; it just starts happening. Topic 02 covers
tracing plain Python functions on top of that with `@traceable`.

## Minimal code

`code.py` confirms your setup works: it sets/reads the three env vars, makes one
`init_chat_model` call (which auto-traces because tracing is on), and prints the project
name plus the LangSmith URL pattern so you know where to go look. Viewing the actual
trace requires a real LangSmith account and API key — the code makes the real call
either way, so if you have a key, a trace genuinely lands in your project.

## Production notes

- One `LANGCHAIN_PROJECT` per environment (`myapp-dev`, `myapp-staging`, `myapp-prod`) —
  never mix dev experimentation traces into the same project a production dashboard
  reads from.
- API keys are scoped to a workspace; treat `LANGCHAIN_API_KEY` like any other secret
  (never commit it — `.env` is already gitignored in this repo's convention).
- You can flip `LANGCHAIN_TRACING_V2` to `false` per-environment without touching code,
  which matters if you ever need to disable tracing quickly (cost, an incident, a
  compliance concern) — it's a config change, not a redeploy.

## Debugging

- No trace appears in the web app → check `LANGCHAIN_TRACING_V2` is the literal string
  `"true"` (not `True`, not `1`), and that `LANGCHAIN_API_KEY` is valid.
- `401`/auth errors at runtime → the key was revoked or copied with extra whitespace.
- Traces land in the wrong project → `LANGCHAIN_PROJECT` wasn't set before the process
  started (env vars are read once at import time in some cases, so restart, don't just
  `export` mid-session).

## Mini challenge

Change `LANGCHAIN_PROJECT` to a new name, rerun `code.py`, and (if you have a LangSmith
account) confirm a brand-new project auto-appears in the web app at
`https://smith.langchain.com/` — projects don't need to be created ahead of time.
