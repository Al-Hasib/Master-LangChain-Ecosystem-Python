# 05 — Retrieval & Answer Validation (Self-Corrective RAG)

## Problem

Every topic so far trusts the agent's final answer at face value. But an agent can call
the right tool, get back thin or tangential context, and still confidently answer as if
the context fully supported it — the model doesn't know what it doesn't know. Phase 4
Topic 08 measured this (groundedness) for a fixed pipeline, after the fact, as an
evaluation metric. This topic runs the same *kind* of check live, inside the loop, so a
bad answer can be caught and retried before it ever reaches the user.

## Concept

Add one more step after the agent produces an answer: ask a second LLM call whether the
retrieved context actually supports that answer. If not, refine the query and give the
agent one more attempt.

```text
Question -> Agent (Topic 02's retriever tool) -> Answer
                    │                               │
                    ▼                               ▼
             tool-call context ────────► Grounded?  (LLM check: context vs answer)
                                              │
                                   ┌──────────┴──────────┐
                                  yes                     no
                                   │                       │
                                   ▼                       ▼
                            return answer          refine query -> retry
                                                    agent ONE more time -> return
```

This is the agent-loop version of Phase 4 Topic 07's "grade documents before
generation" idea, moved one step later: instead of grading retrieved documents *before*
generating, this grades the *finished answer* against what was retrieved, which also
catches cases where retrieval succeeded but the model still overreached beyond it.

The retry is capped at one attempt deliberately — an ungrounded-check loop with no cap
can spin forever on a question the knowledge base genuinely can't answer; one retry
catches "the first query phrasing missed the right doc," not "the doc doesn't exist."

## Minimal code

`code.py` reuses Topic 02's single retriever-tool agent. After it answers, a
`GroundednessCheck` (Pydantic: `grounded: bool`, `reasoning: str`) structured-output call
compares the tool's retrieved context against the final answer. On `grounded=False`, an
LLM rewrites the query to be more specific, the agent is invoked once more with that
refined query, and the result is reported either way — including cases where even the
retry doesn't fully resolve it, which is a real and expected outcome to show on camera.

## Production notes

Groundedness checks add real latency and cost (one extra LLM call minimum, two on a
retry) — reserve them for answers that matter (compliance-sensitive domains, anything
shown to a user without human review) rather than running on every single query in a
high-volume system.

## Debugging

- Grounded check almost always passes, even on answers you know are weak → the grader
  prompt is likely too lenient; ask it to flag anything not *directly and explicitly*
  stated in the context, not just "roughly consistent."
- Retry produces the same ungrounded answer → the refined query probably didn't actually
  change the retrieval results; log the before/after retrieved context, not just the
  before/after query text, to confirm the refinement had any effect.

## Mini challenge

Raise the retry cap from one to two and track, across a handful of questions, how often
the second retry actually changes the groundedness verdict versus just repeating the
first retry's outcome — most systems find diminishing returns past one retry.
