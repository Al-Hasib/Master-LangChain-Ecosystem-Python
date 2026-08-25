# 07 — Auth, Rate Limiting & Caching

## Problem

Topic 03's `/chat` endpoint is open to anyone who can reach it, has no limit on how
often one caller can hit it, and re-runs the (expensive) model call even for a prompt it
just answered a second ago. In production that's an open invitation to run up your model
bill — intentionally (abuse) or not (a buggy client retry-looping).

## Concept

Three independent layers, applied in this order so cheap checks reject a request before
expensive ones run:

```text
request
   │
   ▼
1. Auth        — reject if no/invalid API key           (cheapest check first)
   │
   ▼
2. Rate limit  — reject if this caller is over budget    (still cheap: in-memory counter)
   │
   ▼
3. Cache       — return a stored response if this exact prompt was answered recently
   │            (skips the model call entirely - most expensive step avoided)
   ▼
4. Model call  — only reached if all three above didn't short-circuit it
```

- **Auth** — a FastAPI dependency that checks a request header (`X-API-Key`) against a
  known set of keys, raising `HTTPException(401)` if missing/invalid. Dependencies run
  before the route body, so an unauthenticated request never reaches the model call.
- **Rate limiting** — a **token bucket**: each caller has a bucket that refills at a
  fixed rate; a request costs one token; an empty bucket means `429 Too Many Requests`.
  Simple, in-memory, per-process — correct for a single instance; Topic 06's Redis is
  the production upgrade so the limit is shared across multiple instances instead of
  each one enforcing its own separate budget.
- **Caching** — a dict keyed by a hash of the prompt (`functools` isn't quite right here
  since the key needs hashing/normalizing a string prompt, not memoizing a Python
  function signature) with a TTL, so a repeated prompt returns instantly and for free.
  Topic 06's Redis cache is the same idea, shared across instances and processes.

## Minimal code

`code.py` builds all three, stdlib/in-memory only (no external infra needed to run
this topic's demo): a FastAPI `Depends`-based `require_api_key`, a `TokenBucket` rate
limiter keyed per API key, and a `PromptCache` dict keyed by a SHA-256 hash of the
prompt with a TTL — wired onto a `/chat` endpoint so all three run, in order, before any
model call.

## Production notes

This is the layer that wraps Topic 03's app in the Phase project (Production RAG
Architecture): the API-key check here becomes a real user/tenant lookup, the in-memory
`TokenBucket` becomes a Redis-backed limiter (Topic 06) so the limit holds across
multiple deployed instances, and the in-memory `PromptCache` becomes Topic 06's Redis
cache for the same reason — a `dict` cache gives every instance behind a load balancer a
different, inconsistent view. Never skip auth "for now" on an LLM-backed endpoint — an
open endpoint in front of a paid model API is a direct line to an unbounded bill.

## Debugging

- Rate limit "doesn't work" under real traffic → almost always a per-process `dict`/
  bucket problem: with multiple server processes/instances, each has its own bucket,
  so the effective limit is (per-instance limit × instance count). Move state to Redis.
- Cache returns a stale answer after you fixed a prompt/model bug → the TTL hasn't
  expired yet, or you're not including everything that affects the response (e.g. model
  name, temperature) in the cache key — two different configs sharing one cache entry is
  a correctness bug, not just a staleness one.
- `401` on a request you're sure has the right key → header name mismatch; confirm the
  client sends exactly `X-API-Key` (case-insensitive per HTTP, but the value must match).

## Mini challenge

Extend `TokenBucket` to log (not block) requests that are within 10% of their limit, so
you'd get an early warning signal for a caller about to start being rate-limited, before
it actually starts happening.
