# 02 — Environment Variables & Secrets Management

## Problem

Phase 1 Topic 10's `Settings.from_env()` checked for one key and `sys.exit`-ed with a
friendly message if it was missing — good enough for a single-key teaching example. A
real service has a dozen+ config values, some required, some optional with sane
defaults, some genuinely secret (API keys, DB passwords) and some not (a log level, a
model name). Conflating these, or discovering a missing one mid-request instead of at
startup, is how services end up down at 2am over a typo in a `.env` file.

## Concept

Three rules turn "read some env vars" into a production-grade config layer:

1. **Fail fast, at startup, with a message that says exactly what's missing** — not a
   `KeyError` three requests into serving traffic.
2. **Distinguish required from optional** — optional vars get defaults; required vars
   with no default are a startup error, not a silent `None` that crashes later.
3. **Secrets never live in code or in git** — they live in the environment (`.env`
   locally, a secrets manager in the cloud), and the *file that would contain them*
   (`.env`) is git-ignored while a *template* (`.env.example`) with empty values is
   committed. This repo already does exactly this — check the root `.gitignore` (`.env`
   is excluded) and `.env.example` (keys present, values blank).

```text
.env.example  (committed)         .env  (git-ignored, real values)
OPENAI_API_KEY=          ──copy──►  OPENAI_API_KEY=sk-...
DATABASE_URL=                       DATABASE_URL=postgresql://...
                                            │
                                            ▼
                              Settings.from_env()  <- validates at import/startup
                                            │
                              ┌─────────────┴─────────────┐
                              ▼                            ▼
                     required, missing              optional, missing
                     -> sys.exit(clear msg)          -> use documented default
```

In staging/production this same shape holds, but the "environment" is populated by your
platform (Docker `-e` flags / `env_file`, a cloud provider's secret manager injecting
env vars at container start, Kubernetes `Secret` objects) instead of a `.env` file — the
application code (`Settings.from_env()`) doesn't need to know or care which.

## Minimal code

`code.py` extends Phase 1 Topic 10's `Settings` dataclass with a declarative list of
required vs. optional fields (with defaults), validates all of them in one pass at
startup, and collects *every* missing required var into one error message instead of
failing on the first one — so a developer fixes their `.env` in one pass, not one
`sys.exit` at a time.

## Production notes

At scale, `.env` files are a local-dev convenience only — real secrets in
staging/production come from a managed secrets store (AWS Secrets Manager, GCP Secret
Manager, HashiCorp Vault, or your cloud host's built-in secret injection) so they're
encrypted at rest, access-audited, and rotatable without a code deploy. The `Settings`
dataclass shape doesn't change — only *where* `os.getenv` values ultimately come from.
This is also where the Topic 07 API key and Topic 06 database URL get validated, in the
Phase project's FastAPI service.

## Debugging

- App crashes deep in a request handler with `NoneType has no attribute ...` on
  something config-shaped → a var that should have been required was treated as
  optional; move it to the required list so it fails at startup instead.
- `.env` changes aren't taking effect → confirm `load_dotenv()` runs before any
  `os.getenv()` call, and that you didn't accidentally commit a stale `.env` (check
  `git status` — it should never show `.env` as tracked).

## Mini challenge

Add a `LOG_LEVEL` optional var (default `"INFO"`) and a required `DATABASE_URL` to the
`Settings` class below, then delete `DATABASE_URL` from your local `.env` and confirm
the startup error names it specifically, without needing `OPENAI_API_KEY` to also be
missing to trigger.
