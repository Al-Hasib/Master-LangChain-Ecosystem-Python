# 08 — Retrieval & Groundedness Evaluation

## Problem

Topic 07 filters out documents that are irrelevant to the question — but even with only
relevant documents in context, the model can still say more than the context actually
supports. Asked to elaborate, a capable model will often fill gaps with plausible,
fluent, and *ungrounded* claims — details that sound like they came from the context but
didn't. Grading catches "wrong input," not "output that overreached the input."

## Concept

A **groundedness check** runs *after* generation: given the final answer and the context
it was generated from, does every claim in the answer actually trace back to something
in the context? Like Topic 07's grading, this is an LLM-as-judge call with a structured
(not free-text) output, so it's programmatically actionable:

```python
class GroundednessCheck(BaseModel):
    grounded: bool = Field(description="True only if every claim is supported by the context")
    unsupported_claims: list[str] = Field(description="Claims in the answer NOT found in the context")
    reasoning: str

judge = model.with_structured_output(GroundednessCheck)
result = judge.invoke(f"Context:\n{context}\n\nAnswer:\n{answer}\n\nIs the answer fully grounded?")
```

```text
context + question -> generate -> answer
                                      │
                    context + answer -> groundedness judge -> grounded? unsupported claims?
                                      │
                         not grounded -> flag to user / regenerate with a stricter prompt
```

This is deliberately the *manual, single-example* version of what LangSmith automates at
scale (Phase 9) — running this same style of check across a whole eval dataset, tracked
over time, with dashboards. Here it's one function, run once, so you can see exactly what
the judge is doing before trusting a platform to do it for you across thousands of runs.

**Groundedness vs. relevance grading (Topic 07), not to conflate them:** grading checks
*"was the right context retrieved?"* (an input-quality check, before generation).
Groundedness checks *"does the answer actually stick to what was retrieved?"* (an
output-quality check, after generation). A pipeline can pass grading and still fail
groundedness if the model elaborates beyond well-chosen context.

## Minimal code

`code.py` generates two answers to the same Nimbus question from the same context — one
with a prompt that instructs the model to stick strictly to the context, and one with a
loose prompt that invites it to "be thorough and helpful" (encouraging elaboration) — and
runs the groundedness judge against both, showing the judge catching the second one's
unsupported additions.

## Production notes

Project C (Multi-Document Enterprise RAG) treats grading (07) + groundedness (08) as the
final QC layer before an answer reaches a user — grading upstream of generation,
groundedness downstream of it. At scale, replace this standalone script with LangSmith
evaluators (Phase 9) run against a labeled eval dataset, so groundedness is measured
consistently across every prompt/model/retrieval change instead of spot-checked by hand.

## Debugging

- Judge is inconsistently lenient/strict across runs → set `temperature=0` on the judge
  model and give it an explicit rubric, not just "check if this is grounded."
- Judge flags a well-grounded answer as ungrounded → check if the answer is *paraphrasing*
  context (fine) vs. adding new specifics (not fine) — the rubric needs to distinguish
  these explicitly, since a strict word-for-word check produces too many false positives.
- Groundedness passes but the answer is still wrong → the context itself was
  insufficient or wrong; that's Topic 07's job (grading), not this check's.

## Mini challenge

Feed the groundedness judge an answer generated from *zero* retrieved context (just ask
the model the question directly, no RAG) and confirm it correctly flags the entire
answer as ungrounded, since there's no context for any claim to trace back to.
