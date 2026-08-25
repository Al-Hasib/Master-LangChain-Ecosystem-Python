# 08 — Cost & Latency Optimization

## Problem

"Add caching" and "use a smaller model" are common advice, but without numbers they're
guesses. Topic 07 built a cache; this topic measures what it's actually worth — in
tokens (cost) and wall-clock time (latency) — so optimization decisions are based on
measurement, not vibes.

## Concept

Two independent axes, and they don't always move together:

- **Cost** is (roughly) proportional to tokens in + tokens out, which varies by model.
  Count tokens the same way Phase 0 Topic 02 did (`tiktoken`), before and after a change,
  to see the actual delta — a shorter system prompt or a smaller model can cut cost
  substantially without cutting quality much, but you only know "much" by measuring.
- **Latency** is wall-clock time, and a cache hit is the single biggest latency lever
  available (skips the network call to the model provider entirely) — followed by
  streaming (Topic 04) for *perceived* latency, and model choice (`gpt-4o-mini` vs a
  larger model) for raw latency.

```text
                    tokens in/out          wall-clock time
                    (→ cost)                (→ latency)
no cache, big model      high                   high
no cache, small model    lower                   lower
cache hit (any model)    ~0 (no call made)      ~0 (no network round trip)
```

The right lever depends on what's actually slow/expensive for *your* traffic pattern —
measuring both axes across a couple of real configurations is how you find out, rather
than assuming.

## Minimal code

`code.py` runs the same three prompts through two configurations — `gpt-4o-mini`
without a cache and the same model with Topic 07's `PromptCache` in front of it —
counting tokens with `tiktoken` and timing wall-clock latency for each, then prints a
summary table comparing cost (tokens) and latency (seconds) side by side so the
cache's payoff is a number, not a claim.

## Production notes

Cheapest optimization, in order of effort: (1) cache repeat prompts (Topic 07/06) — 
zero quality tradeoff, pure win when hit rate is nonzero; (2) pick the smallest model
that meets your quality bar for a given task, not the biggest available one; (3) trim
system prompts and conversation history sent per call (Topic 05/06's memory store makes
it easy to accidentally resend a growing history every turn — cap it); (4) batch
independent calls where the workload allows it. Track these numbers over time (e.g. via
LangSmith, Phase 9) so a regression (prompt grew, model changed) is visible before it's
a surprise bill.

## Debugging

- Cache "helps" in this topic's demo but not in production → check your production hit
  rate; a cache only pays off when the same prompts genuinely repeat (common for FAQ-
  style traffic, rare for fully unique user questions).
- Token count doesn't match your provider's billed usage → `tiktoken`'s encoding is an
  approximation for non-OpenAI models and can drift from a provider's exact tokenizer;
  use it for relative comparisons (before/after a change), not exact billing prediction.
- Latency numbers are noisy between runs → network variance is real; average over
  multiple calls rather than trusting a single timed run (this topic's demo does 3).

## Mini challenge

Add a third configuration to the comparison — the same prompts through a larger model
(e.g. `gpt-4o`) — and see how much of the cost/latency delta comes from model size vs.
from caching, to build intuition for which lever to reach for first.
