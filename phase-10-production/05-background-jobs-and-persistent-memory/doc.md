# 05 — Background Jobs & Persistent Memory

## Problem

Two separate problems that both bite the first time a demo becomes a real service:

1. Not all work belongs on the request path. Logging usage, sending a notification, or
   post-processing a response shouldn't make the client wait — but if you just call
   those functions inline, the client *does* wait for them.
2. Every agent so far forgets everything the moment the process restarts — conversation
   history lives in a Python variable, gone on redeploy. A real product needs
   conversation memory that survives restarts.

## Concept

**Background work** — anything that doesn't need to finish before the response is sent
gets pushed off the request path. FastAPI's `BackgroundTasks` is the simplest version:
it runs *after* the response is returned, in the same process:

```text
request  ──►  do the real work (agent call)  ──►  return response to client
                                                            │
                                                            ▼ (after response is sent)
                                              background task runs: log usage, etc.
```

`BackgroundTasks` runs in-process and is lost if the process crashes before the task
runs — fine for cheap, best-effort work (logging, analytics). Genuinely durable
work (must survive a crash, must retry) belongs in a real task queue (Celery, RQ, or a
cloud provider's managed queue) backed by Redis or a database — out of scope for this
topic's minimal example, but the pattern (enqueue now, process separately) is the same.

**Persistent memory** — instead of holding conversation history in memory, store it
keyed by `session_id` in a database. SQLite is enough for this topic (single file, no
server to run) — Topic 06 does the same thing against Postgres for a real
multi-instance deployment:

```text
session_id  ──►  SELECT messages FROM conversations WHERE session_id = ?
                          │
                          ▼
              prior turns + new turn  ──►  agent.invoke(...)
                          │
                          ▼
              INSERT new turn back into the table
```

## Minimal code

`code.py` has two independent parts: (1) a FastAPI endpoint using `BackgroundTasks` to
log request usage after responding, and (2) a `SQLiteMemoryStore` class
(`sqlite3`, stdlib only) that saves/loads conversation turns by `session_id`, wired into
a small `main()` that shows a conversation surviving across two separate "process"
instantiations of the store (simulating a restart).

## Production notes

This is where the Phase project's "persistent memory" comes from — Topics 05 and 06
together: this topic's SQLite pattern generalizes directly to Topic 06's Postgres-backed
store for a real deployment (multiple API instances can't share a SQLite file safely,
but they can share a Postgres database). For background work that must survive a
crash or needs retries/scheduling, graduate from `BackgroundTasks` to a real queue
(Celery/RQ + Redis, or a cloud task queue) — the enqueue-then-process shape doesn't
change, only the durability guarantee.

## Debugging

- Background task never runs → confirm you called `background_tasks.add_task(fn, ...)`
  and returned the `BackgroundTasks` param from the route (FastAPI wires it via
  dependency injection on the parameter, not a decorator).
- Memory "resets" between requests even with the SQLite store wired in → check you're
  opening a new connection per call, not holding one file handle across requests without
  committing (`conn.commit()`), and that `session_id` matches on every call.
- `database is locked` errors under concurrent access → expected SQLite behavior under
  concurrent writers; this is the exact reason Topic 06 moves to Postgres for anything
  beyond a single-instance demo.

## Mini challenge

Add a background task that also writes a `last_active` timestamp to the SQLite store, so
you can later report which sessions are "warm" (recently active) without slowing down
the actual chat response for it.
