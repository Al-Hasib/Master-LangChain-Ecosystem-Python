# 06 — Databases: PostgreSQL & Redis

## Problem

Topic 05's SQLite store proved persistent memory works, but SQLite is a single file —
it can't be shared safely by multiple API instances (the normal shape of a deployed
service behind a load balancer), and it has no concept of a fast, shared, ephemeral
cache. Production services split these two jobs across two different databases because
they have different jobs: **Postgres** for durable, structured, relational data;
**Redis** for fast, ephemeral, shared-across-instances state.

## Concept

```text
      N API instances (Topic 10: containers, load-balanced)
      │           │           │
      └───────────┼───────────┘
                   │
      ┌────────────┴─────────────┐
      ▼                           ▼
  PostgreSQL                    Redis
  - conversation history        - response cache (Topic 07)
  - durable, relational         - rate-limit counters (Topic 07)
  - survives restarts           - fast, in-memory, shared
  - one source of truth         - can be evicted/lost - not the source of truth
```

Why not just use one: SQLite (Topic 05) can't be shared between processes/instances
safely for concurrent writes. Redis is fast but not meant to be durable storage — data
can be evicted or lost on restart depending on configuration, which is fine for a cache
or rate-limit counter (recomputable) but wrong for conversation history (not
recomputable). Postgres is the source of truth; Redis is an accelerator in front of it.

For LangGraph specifically, `langgraph-checkpoint-postgres` (a separate package) provides
`PostgresSaver`, a `BaseCheckpointSaver` that persists a graph's state to Postgres so a
LangGraph agent's execution state survives restarts and resumes exactly where it left
off — the graph-native equivalent of Topic 05's SQLite store, but for LangGraph state
rather than plain chat turns, and safe for multiple instances to share. This topic's
`code.py` keeps to plain `psycopg` (matching the rest of this phase's non-LangChain-
specific focus) — see the sidebar in `code.py`'s comments for how `PostgresSaver` would
plug in instead.

## Minimal code

`code.py` has two independent, real client examples: a `psycopg`-based
`PostgresConversationStore` (parallel structure to Topic 05's SQLite store, but backed by
a real Postgres table) and a `redis`-based `ResponseCache` (get/set with a TTL, keyed by
a hash of the prompt). Both wrap their connection attempt in `try/except`, catching the
connection error specifically and printing the exact `docker run` command to start a
local instance — this sandbox has neither database running, so the code is real but the
demo degrades to clear instructions instead of a crash.

## Production notes

This is the persistence layer under the Phase project: Postgres holds conversation
memory (replacing Topic 05's SQLite for a multi-instance deployment) and, if the app
uses LangGraph directly, agent checkpoints via `PostgresSaver`; Redis backs Topic 07's
cache and rate limiter so those work correctly across multiple API instances instead of
per-process (an in-memory `dict` cache is per-process and gives each instance a
different, inconsistent view). Both are provisioned as managed services in most cloud
deployments (RDS/Cloud SQL for Postgres, ElastiCache/Memorystore for Redis) rather than
self-hosted containers.

## Debugging

- `psycopg.OperationalError: connection refused` → Postgres isn't running; start one
  locally with `docker run -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres` (see
  `code.py`'s except block for the exact message this topic prints).
- `redis.exceptions.ConnectionError` → same story for Redis:
  `docker run -p 6379:6379 redis`.
- Data "disappears" from Redis but not Postgres → expected — Redis is a cache, not a
  source of truth; never store something there that can't be recomputed or re-fetched
  from Postgres.

## Mini challenge

Once you have Docker running locally, start both containers from the commands above,
re-run `code.py`, and confirm the "connection refused" fallback paths are replaced by
real reads/writes — then kill the Redis container mid-run and confirm the app degrades
gracefully rather than crashing (a well-designed cache layer should be optional).
