# Phase 10 — Production AI Engineering

**Status:** 🗒️ Topic list only — ask for this phase by name to have it fully built out.

**This is the phase that separates a beginner playlist from a professional one** — the
engineering around the model calls, not the model calls themselves.

## Topics

01. **AI Application Architecture Overview** — the north-star architecture the whole course has been building toward.
02. **Environment Variables & Secrets Management** — safe config across dev/staging/prod.
03. **API Design with FastAPI** — exposing a LangChain/LangGraph app as an HTTP API.
04. **Streaming APIs & Async Execution** — streaming tokens/events over HTTP, async agent execution.
05. **Background Jobs & Persistent Memory** — long-running work off the request path; durable conversation memory.
06. **Databases: PostgreSQL & Redis** — persistence for memory/checkpoints (Postgres) and caching/rate-limit state (Redis).
07. **Auth, Rate Limiting & Caching** — protecting an LLM-backed API from abuse and runaway cost.
08. **Cost & Latency Optimization** — token optimization, model selection, caching, batching.
09. **Evaluation in CI/CD & Testing Agents** — running LangSmith evaluations as a CI gate; unit-testing agent behavior.
10. **Deployment: Docker & Cloud** — containerizing the app and deploying (incl. LangSmith Deployment for LangGraph/Deep Agents apps).

## Phase project

**Production RAG Architecture** — the Phase 9 observable RAG agent, wrapped in a
FastAPI service with auth, caching, Postgres-backed memory, Dockerized, and deployed.
