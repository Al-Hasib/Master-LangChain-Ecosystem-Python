# 10 — Deployment: Docker & Cloud

## Problem

Every topic in this phase still only runs on your machine via `python code.py`. To
actually ship the Phase project (the Production RAG Architecture) to users, it needs to
run the same way on any machine — a teammate's laptop, a CI runner, a cloud VM — without
"works on my machine" surprises from Python version drift or missing system packages.

## Concept

Docker solves "runs the same everywhere" by packaging the app, its exact dependencies,
and a minimal OS layer into one portable image:

```text
Dockerfile          →  docker build  →  image  →  docker run  →  running container
(recipe: base image,                  (immutable,             (the app, isolated,
 deps, code, start                     versioned                listening on a
 command)                              artifact)                 mapped port)
```

For a real deployment, the app (Topic 03's FastAPI service) usually isn't the only
container — it needs Postgres (Topic 06) and Redis (Topic 06) alongside it.
`docker-compose.yml` describes all three as one unit so `docker compose up` starts the
whole stack with correct networking between them (containers reach each other by
service name, e.g. the app connects to `postgres://db:5432`, not `localhost`):

```text
docker-compose.yml
  ├── app       (this phase's FastAPI service, built from Dockerfile)
  ├── postgres  (Topic 06 - conversation memory)
  └── redis     (Topic 06/07 - cache, rate-limit state)
        all on one Docker network - service names resolve as hostnames
```

From there, "cloud deployment" is running the same image on a managed container
platform (AWS ECS/Fargate, GCP Cloud Run, Azure Container Apps, Render, Fly.io, ...)
instead of your own machine — the image doesn't change; only where it runs does. For a
LangGraph-based app specifically, LangSmith Deployment (Phase 9's LangSmith, extended)
is a managed option purpose-built for LangGraph apps — conceptual for this course; the
Docker path above is the portable, provider-agnostic default this topic teaches.

## Minimal code

This topic ships three real files alongside `doc.md`: `Dockerfile` (multi-stage-free,
single-stage build of Topic 03's FastAPI app — kept simple and correct rather than
optimized), `docker-compose.yml` (app + postgres + redis, wired together), and
`code.py`, which does NOT run Docker (not available in this sandbox) — it statically
validates that both files are syntactically sane (the Dockerfile has required
instructions in a sane order; the compose file is valid YAML with the expected
services) and prints the exact commands a developer would run next.

## Production notes

This is the last mile for the Phase project: containerize Topic 03's app (with Topics
04/07 folded in), point its `DATABASE_URL`/`REDIS_URL` env vars (Topic 02) at the
`postgres`/`redis` services from `docker-compose.yml` (locally) or managed instances
(in the cloud), and deploy the resulting image. Keep the image small (a slim Python
base, `.dockerignore` excluding `.venv`/`__pycache__`/`.env`) and never bake secrets
into the image itself — they're injected as environment variables at container start
(Topic 02), the same way `.env` injects them locally.

## Debugging

- `docker build` fails on `pip install` → almost always a missing system dependency for
  a compiled wheel; pin versions in `requirements.txt` and use a base image
  (`python:3.11-slim`) that has the common build tools, or switch to a package with
  prebuilt wheels (e.g. `psycopg[binary]`, already used in Topic 06).
- App container can't reach Postgres/Redis → inside Docker Compose, use the **service
  name** as the hostname (`postgres`, `redis`), never `localhost` — `localhost` inside a
  container refers to the container itself, not its neighbors.
- Container exits immediately after starting → check the `CMD`/entrypoint actually
  starts a long-running process (`uvicorn ... `) rather than a one-shot script, and that
  it binds to `0.0.0.0`, not `127.0.0.1` (which isn't reachable from outside the
  container).

## Mini challenge

Once Docker is available to you, run `docker compose up --build` against this topic's
files, then `curl` the health endpoint from Topic 03/07 through the mapped port, and
confirm the app can actually reach the `postgres`/`redis` services by service name.
