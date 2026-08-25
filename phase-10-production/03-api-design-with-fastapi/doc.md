# 03 — API Design with FastAPI

## Problem

Everything built so far only runs on your machine, in your terminal, one invocation at a
time. To let a frontend, a mobile app, or another service use your agent, it needs to be
reachable over HTTP — a stable contract (request/response shape) that doesn't change
just because you refactored the LangChain code behind it.

## Concept

FastAPI is the standard choice for wrapping an LLM-backed app: it's async-native (Topic
04 needs this), validates request/response shapes with Pydantic (which LangChain already
depends on, so there's no new mental model), and generates interactive docs for free.

The shape of a minimal LLM API endpoint:

```text
POST /chat  {"message": "...", "session_id": "..."}
        │
        ▼
  Pydantic request model   <- validates shape BEFORE your code runs
        │
        ▼
  FastAPI route handler
        │
        ▼
  agent.invoke(...) / model.invoke(...)   <- the part every prior phase built
        │
        ▼
  Pydantic response model  <- guarantees a stable shape back to the client
```

Two design choices matter more for an LLM API than a typical CRUD API:

- **Validate input strictly** — a request model with a bounded `message: str` (e.g. max
  length) protects you from a client sending a 50,000-token prompt that blows your cost
  budget before Topic 07's auth/rate-limiting even gets involved.
- **Keep the response model stable even as the agent changes** — return a shaped
  `ChatResponse{reply, session_id}`, not the raw LangGraph state dict, so swapping models
  or adding tools (any later phase) never breaks a client integration.

## Minimal code

`code.py` wraps a single `create_agent(...)` call in a FastAPI app with one
`POST /chat` endpoint: a Pydantic `ChatRequest`/`ChatResponse` pair, a `GET /health`
endpoint (standard for any deployed service — Topic 10's Docker/orchestrator health
checks depend on this existing), and a `main()` that starts the app with `uvicorn.run(...)`
so `python code.py` serves it directly.

## Production notes

This is the entry point the Phase project (Production RAG Architecture) builds on:
Topic 07's auth/rate-limit/cache wrap this same app as FastAPI dependencies, Topic 06's
Postgres backs per-`session_id` memory instead of this topic's stateless call, and
Topic 10 containerizes exactly this file. Keep route handlers thin — request validation
and response shaping only; agent construction and business logic stay in their own
functions (or modules, per Phase 1 Topic 10's structure) so they're unit-testable
without spinning up FastAPI at all.

## Debugging

- `uvicorn code:app` fails with `Error loading ASGI app` → the module-level variable
  must be literally named `app` (a `FastAPI()` instance), not wrapped inside a function.
- A request "hangs" → you're calling a blocking `.invoke()` inside an `async def` route
  without `await` or a thread offload; see Topic 04 for the async-correct version.
- `422 Unprocessable Entity` on a request that looks right → check the Pydantic model
  field names/types match the JSON body exactly; FastAPI's `/docs` page shows the exact
  schema it expects.

## Mini challenge

Add a second endpoint, `GET /docs-check`, that returns the OpenAPI schema's endpoint
count (`app.openapi()["paths"]`), to see how FastAPI derives full API docs from the
Pydantic models you already wrote for validation.
