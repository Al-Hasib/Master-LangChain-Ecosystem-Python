# 09 — LangGraph Runtime & Production Architecture

## Problem

Every example so far runs in one Python process, keeps state in RAM (`InMemorySaver`),
and starts fresh each time you run `python code.py`. That's the right way to *learn* the
mechanics — it's the wrong way to *run* something real users depend on. What actually
changes going from a local script to a deployed graph?

## Concept

Four things change, and they're mostly swaps, not rewrites — because everything in this
phase was already built around a compile-time boundary (checkpointer, store) instead of
hardcoding storage inside nodes:

1. **Checkpointer backend** — `InMemorySaver()` → a durable saver (Postgres-backed,
   etc.). Same `compile(checkpointer=...)` call site, same node code, different object.
2. **Process model** — one long-lived `python code.py` process → a server process (the
   LangGraph runtime/platform) that loads your compiled graph and serves `.invoke()` /
   `.stream()` over HTTP, handling many threads/users concurrently instead of one script
   run.
3. **Long-running / paused work** — Topic 06's interrupts assumed the process could sit
   there waiting; in production, a paused thread should survive the *server* restarting,
   scaling down, or a deploy going out — which is exactly what a durable checkpointer
   guarantees and `InMemorySaver` doesn't.
4. **Observability** — instead of `print()`-ing state at each step (this whole phase),
   production graphs get traced automatically (Phase 9, LangSmith) so you can inspect any
   real run's node-by-node history after the fact, not just while it's running in front
   of you.

```text
LOCAL (this phase's code.py files)          PRODUCTION
─────────────────────────────────           ─────────────────────────────────
one-off `python code.py` run                long-lived server process
InMemorySaver (RAM, gone on exit)           durable checkpointer (Postgres, ...)
print(state) to see what happened           traces in LangSmith (Phase 9)
you resume interrupts by hand, same run     resume arrives later, maybe different process
```

## Minimal code

`code.py` is a small **readiness checklist** script, not new graph mechanics — it takes
Topic 03's classify-then-route graph, inspects how it was compiled, and prints a
pass/fail report against the four production concerns above (durable checkpointer
configured? etc.), so the checklist is something you can point at a real graph, not just
read about.

## Production notes

Don't reach for a deployed LangGraph runtime before you need one — most of this course's
projects run fine as a script or behind a plain FastAPI endpoint (Phase 10) that calls
`.invoke()`/`.stream()` directly. Reach for the managed runtime once you need built-in
horizontal scaling, managed durable execution, or a team of non-Python people triggering
runs through an API without touching your codebase.

## Debugging

- "Works locally, loses state in production" → almost always `InMemorySaver` was never
  swapped for a durable backend before deploying.
- "Interrupted runs never resume in production" → the resume request isn't reaching the
  same durable-state backend the original run paused into (e.g. two environments pointed
  at different databases).

## Mini challenge

Take Topic 04's checkpointed chat graph and write down (in a comment, no need to actually
provision infra) exactly which one line would change to point it at a durable
checkpointer instead of `InMemorySaver` — confirm it's genuinely only that one line.
