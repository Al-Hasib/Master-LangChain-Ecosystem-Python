# 08 — Monitoring & Production Observability

## Problem

Tracing (Topics 02–03) helps you debug *one run you're already looking at*. Production
raises a different question: across **thousands** of runs a day, is the app getting
slower? More expensive? Failing more often for some subset of users? You can't answer
that by opening traces one at a time — you need aggregates over time, i.e. monitoring.

## Concept

LangSmith's monitoring is the same traces from Topics 02–03, rolled up over time into
dashboards: latency percentiles (p50/p95/p99), token/cost totals, error rate, and
run-volume — sliceable by `metadata` you attached when tracing (per Topic 02's production
notes: `user_id`, `session_id`, `tool_version`, etc.), plus **alerting** on top (e.g.
"page someone if error rate exceeds 5% over 10 minutes").

```text
every traced run  ──────────────►  LangSmith stores it
        │                                  │
        ▼                                  ▼
  (Topics 02-03: inspect                monitoring dashboards
   ONE run's tree)                      (aggregate over ALL runs):
                                          - latency p50/p95/p99 over time
                                          - $ cost over time (from token counts)
                                          - error rate over time
                                          - volume, sliced by metadata
                                          - alerts on thresholds
```

This is a **hosted web-app feature** — dashboards, alert rules, and cost-over-time charts
render in the LangSmith UI itself and genuinely can't be replicated by a terminal script.
What a script *can* do, and what `code.py` does here, is compute the same two raw
ingredients LangSmith's dashboards are built from — **latency** and **token
count/estimated cost** — locally, per call, as a stand-in you can read right in the
terminal. It's the same idea at a tiny scale: no history over time, no percentiles across
thousands of runs, no alerting, just proof of what the numbers underneath a dashboard
actually are.

## Minimal code

`code.py` makes a handful of LLM calls, timing each with `time.perf_counter()` and
counting tokens with `tiktoken` (already used for OpenAI models in Phase 1), then prints
a small local summary: total latency, average latency, total tokens, and an estimated
cost using a hardcoded (and clearly-labeled-as-approximate) per-token price. If a
LangSmith key is present, the same calls are traced too — pointing out that in a real
deployment, this exact data is what feeds the hosted dashboard instead of a `print()`.

## Production notes

- Don't hand-roll cost tracking for a real production system — LangSmith's cost tracking
  reads token usage directly off traced runs and stays correct as pricing changes,
  without you maintaining a price table in code (the one in `code.py` is a rough
  teaching stand-in, not something to actually ship).
- Set alert rules on error rate and p95 latency, not just averages — an average can look
  fine while a meaningful fraction of users have a broken/slow experience.
- Use `metadata` (Topic 02) consistently in production so a dashboard can be sliced by
  `deployment_version`, `model`, or `customer_tier` — retrofitting metadata onto old
  traces isn't possible, so this is a "get it right from day one" concern.

## Debugging

- Local latency looks fine but users report slowness → check you're timing the whole
  round trip (including retries/fallbacks from Phase 1 Topic 08's middleware) not just
  the final successful call.
- Token counts here don't match LangSmith's dashboard exactly → `tiktoken` estimates
  locally from the prompt text; LangSmith's numbers come from the provider's actual
  usage response, which is the authoritative source, not the local estimate.
- Cost estimate is off → prices change; the constant in `code.py` is explicitly a
  snapshot-in-time approximation, not a source of truth.

## Mini challenge

Run `code.py` twice — once with a short prompt, once with a much longer one — and
compare the printed latency/token/cost numbers, to build intuition for how directly
prompt length drives both cost and latency (something a real dashboard would show you
as a trend over thousands of runs instead of two).
