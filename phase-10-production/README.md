# Phase 10 — Production AI Engineering

**Status:** ✅ Fully built — every topic has doc.md and code.py.

**This is the phase that separates a beginner playlist from a professional one** — the
engineering around the model calls, not the model calls themselves.

## Topics

01. [AI Application Architecture Overview](01-ai-application-architecture-overview/doc.md) — the north-star architecture the whole course has been building toward.
02. [Environment Variables & Secrets Management](02-environment-variables-and-secrets-management/doc.md) — safe config across dev/staging/prod.
03. [API Design with FastAPI](03-api-design-with-fastapi/doc.md) — exposing a LangChain/LangGraph app as an HTTP API.
04. [Streaming APIs & Async Execution](04-streaming-apis-and-async-execution/doc.md) — streaming tokens/events over HTTP, async agent execution.
05. [Background Jobs & Persistent Memory](05-background-jobs-and-persistent-memory/doc.md) — long-running work off the request path; durable conversation memory.
06. [Databases: PostgreSQL & Redis](06-databases-postgresql-and-redis/doc.md) — persistence for memory/checkpoints (Postgres) and caching/rate-limit state (Redis).
07. [Auth, Rate Limiting & Caching](07-auth-rate-limiting-and-caching/doc.md) — protecting an LLM-backed API from abuse and runaway cost.
08. [Cost & Latency Optimization](08-cost-and-latency-optimization/doc.md) — token optimization, model selection, caching, batching.
09. [Evaluation in CI/CD & Testing Agents](09-evaluation-in-cicd-and-testing-agents/doc.md) — running LangSmith evaluations as a CI gate; unit-testing agent behavior.
10. [Deployment: Docker & Cloud](10-deployment-docker-and-cloud/doc.md) — containerizing the app and deploying (incl. LangSmith Deployment for LangGraph/Deep Agents apps).

## Running the examples

```bash
pip install -r ../requirements.txt   # uncomment the fastapi/uvicorn/psycopg/redis lines first
cp ../.env.example ../.env           # fill in OPENAI_API_KEY at minimum
python 01-ai-application-architecture-overview/code.py
```

Some topics (03, 04, 05, 07) run a FastAPI app — use `uvicorn code:app --reload` from
inside the topic folder, or just `python code.py` (each wires `uvicorn.run(...)`
internally so it also works standalone). Topics 06 and 10 need Postgres/Redis/Docker
running locally to fully exercise — each prints exact `docker run`/`docker compose`
commands and degrades to clear setup instructions instead of crashing if that infra
isn't available.

## Phase project

**Production RAG Architecture** — the Phase 9 observable RAG agent, wrapped in a
FastAPI service with auth, caching, Postgres-backed memory, Dockerized, and deployed.
