# 06 — LLM-as-a-Judge: RAG & Agent Evaluation

## Problem

Topic 05's `contains_expected_number` evaluator works because the "right answer" is a
short exact string. Most real answers aren't like that — a RAG answer can be *correct in
substance but phrased differently* than any reference string, and an agent's "success" at
a multi-step task isn't a string-match question at all ("did it actually book the right
flight?"). You need a scorer that can judge *meaning*, not just equality — which means
using another LLM as the scorer.

## Concept

An LLM-as-a-judge evaluator is a structured-output call (Phase 1 Topic 04's pattern)
where the "extracted data" is a **score + reasoning** instead of business data:

```python
from pydantic import BaseModel, Field

class JudgeResult(BaseModel):
    """A judge's verdict on one answer."""
    score: bool = Field(description="True if the answer meets the grading criteria")
    reasoning: str = Field(description="One sentence explaining the score")

judge_model = model.with_structured_output(JudgeResult)
```

Two grading criteria this topic covers, both fed by the same pattern with a different
prompt:

- **Groundedness (RAG)** — does the answer's claims actually appear in the retrieved
  context, or did the model add unsupported facts ("hallucinate")? The judge sees
  `(context, answer)` and checks the answer against the context — not against outside
  knowledge.
- **Task success (agent)** — given the original task and the agent's final answer (and
  optionally its tool-call trace), did it actually accomplish what was asked? The judge
  sees `(task, final_answer)` and checks whether the outcome satisfies the request.

```text
groundedness judge:  (context, answer)      -> JudgeResult(score, reasoning)
task-success judge:  (task, final_answer)   -> JudgeResult(score, reasoning)
```

Both are just evaluator functions in the Topic 05 sense — they can be passed straight
into `evaluate()` (Topic 07) as `evaluators=[groundedness_judge, task_success_judge]`,
scoring an entire dataset automatically instead of one answer at a time.

## Minimal code

`code.py` builds the Topic 02-style minimal RAG pipeline, asks it a question, then runs a
**groundedness judge** against `(retrieved context, generated answer)`. Separately, it
runs a tiny agent (Topic 03-style) on a task and runs a **task-success judge** against
`(task, final answer)`. Both judge calls use `with_structured_output(JudgeResult)` and, if
`LANGCHAIN_API_KEY` is set, are themselves traced — a judge call is a real LLM call and
shows up in LangSmith like any other.

## Production notes

- Use a cheaper/faster model for the judge than the one being judged when possible —
  judging is usually a simpler task than generating, and running a judge over an entire
  production dataset repeatedly adds up in cost.
- Always keep `reasoning` in the schema, not just `score` — a bare pass/fail number with
  no explanation is nearly impossible to debug when the judge itself is wrong (judges are
  not perfect and need spot-checking against human review periodically).
- Log disagreements between the judge and a human reviewer as their own dataset — that's
  how you calibrate/improve the judge prompt over time.

## Debugging

- Judge scores everything as "pass" regardless of quality → the grading criteria in the
  judge's prompt is too vague ("is this a good answer?" instead of "does every factual
  claim in the answer appear in the context?").
- Judge is inconsistent across runs → set `temperature=0` on the judge model; grading
  should be as deterministic as you can make it.
- Groundedness judge flags a correct answer as ungrounded → check whether the context
  passed to the judge actually matches the context the *original* answer was generated
  from (a common bug: re-retrieving instead of reusing the same context).

## Mini challenge

Add a third judge criterion — conciseness (does the answer stay under N sentences?) —
as its own `JudgeResult`-shaped evaluator, and run all three judges against the same
RAG answer to see them disagree (an answer can be grounded and correct, but not concise).
