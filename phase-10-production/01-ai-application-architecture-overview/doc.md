# 01 — AI Application Architecture Overview

## Problem

Every phase so far has ended at `model.invoke(...)` or `agent.invoke(...)` printing to a
terminal. Nothing about that is a *product* — no client can call it, nobody but you can
run it, a crash takes down your only process, and an expensive prompt gets sent every
time someone repeats a question. Phase 10 is about everything that sits **around** the
call you've already mastered.

## Concept

None of the remaining topics are LangChain-specific — they're standard backend
engineering, applied to an app whose core unit of work happens to be an LLM call. The
north-star architecture this whole phase builds toward, one layer per topic:

```text
                         ┌─────────────────────────┐
        request  ──────► │  Auth + Rate Limit  (07) │
                         └────────────┬─────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │   FastAPI app    (03)    │──── async / streaming (04)
                         └────────────┬─────────────┘
                                      ▼
                    ┌───────────┬──────────┬─────────────┐
                    ▼           ▼          ▼             ▼
               Cache (07)  Background   LangChain /   Cost & latency
                            jobs (05)   LangGraph      tracking (08)
                                        agent call
                                              │
                                              ▼
                              ┌───────────────────────────┐
                              │  Postgres (memory/state)   │
                              │  Redis (cache/rate state)  │  (06)
                              └───────────────────────────┘
                                              │
                                              ▼
                              CI evaluation gate (09) ── Docker / cloud deploy (10)
```

Every box above is a *concern*, not a file — in a real project most of them are their
own module (see Phase 1 Topic 10's project-structure pattern), and several compose
directly into this phase's project:

- **Config** (Topic 02) underlies every other box — nothing above should read
  `os.environ` directly except at startup.
- **The FastAPI app** (Topic 03) is the front door; **auth/rate-limit/cache** (Topic 07)
  wrap it before a request ever reaches your agent.
- **Streaming and async** (Topic 04) change *how* the app talks to the model without
  changing *what* it computes.
- **Background jobs and memory** (Topic 05) and the **databases** behind them
  (Topic 06) make the app stateful and let slow work happen off the request path.
- **Cost/latency optimization** (Topic 08) and **CI evaluation** (Topic 09) are the
  feedback loops that keep the shipped app good and affordable.
- **Docker/deployment** (Topic 10) is how all of the above actually reaches a user.

## Minimal code

`code.py` is *not* a working app — it's an "architecture as code" skeleton: a
config-driven `App` object with one method stub per concern above, each stub containing
only a comment pointing at the topic that fills it in for real. Running it prints the
request lifecycle in the order the layers would actually execute, so you can see the
shape before any topic supplies the substance.

## Production notes

Resist building all of this before you have a user. Topics 02–04 (config, API,
streaming) are close to always-needed. Topics 05–07 (jobs, databases, auth/caching)
earn their complexity once you have real traffic or real cost to control. Topic 08–09
(optimization, CI evals) matter once you have a baseline to protect from regressing.
Topic 10 (deployment) is the last mile, not the first.

## Debugging

If you can't tell which topic a bug belongs to, place it on this diagram first — "the
response is stale" is a Topic 07 (cache) bug, "the response is slow" is a Topic 08 bug,
"the response is gone after a restart" is a Topic 05/06 (persistence) bug. Localizing a
bug to a layer is most of the fix.

## Mini challenge

Sketch (on paper or in comments) which of these layers *your own* Phase 9 RAG agent is
currently missing, and rank them by which would break first under real traffic.
