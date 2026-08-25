# 08 — Parallel Agents & Collaboration

## Problem

Every multi-agent example so far (Topics 06-07) runs agents one after another - a
research agent, then a writer agent, then a supervisor calling tools in sequence.
When several agents don't actually depend on each other's output (e.g. three agents
each answering the same question from a different angle), running them sequentially
just adds up their latencies for no reason.

## Concept

**Fan-out / fan-in**: dispatch the same input to multiple agents at once, let them run
concurrently, then merge their outputs into one result. Because `agent.invoke()` is a
synchronous, blocking network call (waiting on the LLM API), this is a textbook case for
`concurrent.futures.ThreadPoolExecutor` - Python's stdlib thread pool. Threads, not
`asyncio`, because nothing here needs an async rewrite of the agent code: each thread
just blocks on its own `invoke()` call, and the GIL releases during I/O wait, so the
requests genuinely overlap in wall-clock time.

```text
              ┌──► Agent A (optimistic framing)  ──┐
question ─────┼──► Agent B (skeptical framing)   ──┼──► merge step ──► combined answer
              └──► Agent C (concise framing)     ──┘
        (fan-out, concurrent)                  (fan-in, sequential)
```

The merge step is itself just another model call (or another agent) - given all the
individual answers, produce one combined view. Fan-in is inherently sequential (you
need every fan-out result before you can merge), so only the fan-out half is
parallelized.

## Minimal code

`code.py` builds three agents that share a system-prompt template but each get a
different "lens" (optimistic / skeptical / concise), fires the same question at all
three concurrently via `ThreadPoolExecutor`, times how long the fan-out took vs. what
sequential execution would have taken, then merges the three answers with one more
model call.

## Production notes

Cap concurrency (`ThreadPoolExecutor(max_workers=...)`) to stay under your model
provider's rate limits - unbounded fan-out across many agents can trigger 429s. Handle
per-agent failures independently (wrap each `future.result()` in try/except) so one
agent erroring doesn't take down the whole fan-in; merge whatever succeeded and note
what didn't.

## Debugging

- No actual speedup observed → confirm you're calling `.submit()` for all agents
  *before* calling `.result()` on any of them - calling `.result()` immediately after
  each `.submit()` serializes the work again.
- One slow agent holds up the whole batch → that's expected with this pattern (fan-in
  waits for all); add a per-future `timeout` to `.result()` if partial results are
  acceptable.

## Mini challenge

Add a fourth "lens" agent and a `timeout=` on each `future.result()` call; have the
merge step note which agent(s), if any, didn't respond in time.
