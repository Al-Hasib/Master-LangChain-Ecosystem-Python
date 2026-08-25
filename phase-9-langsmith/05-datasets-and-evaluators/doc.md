# 05 — Datasets & Evaluators

## Problem

Manually eyeballing "does this answer look right?" doesn't scale, and it doesn't catch
regressions — you'd have to remember every question you ever tried and re-ask them by
hand after every change. You need a fixed, reusable set of question/expected-answer pairs
you can re-run automatically, plus a function that scores each answer against its
expected value.

## Concept

A **dataset** is just a named collection of **examples**, where each example is an
`inputs` dict and an (optional) `outputs` dict holding the expected/reference answer:

```python
from langsmith import Client

client = Client()
dataset = client.create_dataset(
    dataset_name="phase9-qa-golden-set",
    description="Small golden set for regression-testing the course RAG example.",
)
client.create_examples(
    dataset_id=dataset.id,
    examples=[
        {"inputs": {"question": "What is a retriever?"},
         "outputs": {"answer": "A component that fetches relevant documents for a query."}},
        # ...more examples...
    ],
)
```

This is exactly the same shape as a Python list of dicts — which is the point: a
LangSmith dataset *is* a hosted, versioned, re-runnable list of dicts. Anything you'd
otherwise keep as a local `TEST_CASES = [...]` list maps directly onto this.

An **evaluator** is a function that scores one run against its example. The signature
LangSmith's `evaluate()` (Topic 07) expects is `(run, example) -> dict`:

```python
from langsmith.schemas import Run, Example

def exact_match(run: Run, example: Example) -> dict:
    predicted = run.outputs["answer"]
    expected = example.outputs["answer"]
    return {"key": "exact_match", "score": predicted.strip() == expected.strip()}
```

`run` is the traced run your app produced (its `.outputs` is whatever your app
returned); `example` is the dataset row (its `.outputs` is the reference answer). The
returned dict's `"key"` names the metric (shown as a column in the UI) and `"score"` is
the metric's value (bool, int, or float).

```text
dataset (examples: inputs + reference outputs)
        │
        ▼
  your app runs on each example.inputs  ──►  run.outputs
        │                                         │
        ▼                                         ▼
              evaluator(run, example) -> {"key": ..., "score": ...}
                        │
                        ▼
              aggregated per-example AND per-experiment in LangSmith
```

## Minimal code

`code.py` builds a tiny 3-question golden set for a unit-conversion-style task, and
writes one custom evaluator (`contains_expected_number`) that checks whether the app's
answer contains the expected numeric value. If `LANGCHAIN_API_KEY` is set, the dataset is
genuinely created in your LangSmith workspace via `create_dataset`/`create_examples`;
either way, the same list of dicts is used locally to prove the evaluator logic works,
since actually *running* the evaluator through `evaluate()` against a live experiment is
Topic 07's job.

## Production notes

- Keep a *small*, hand-curated "golden set" (10–50 examples) that's reviewed like code,
  separate from any large auto-sampled dataset pulled from production traffic.
- Store `metadata` on each example (e.g. `{"difficulty": "hard"}`) so you can later slice
  evaluation results by category, not just an overall pass rate.
- Prefer several narrow evaluators (`exact_match`, `mentions_all_entities`,
  `is_concise`) over one giant scoring function — narrow evaluators show up as separate
  columns and make regressions easy to attribute.

## Debugging

- `create_examples` succeeds but examples don't appear under the dataset in the UI →
  double check `dataset_id` matches the dataset you actually created (a typo'd/stale ID
  silently creates orphaned examples against nothing you can find).
- Evaluator always returns the same score → you're likely comparing the wrong fields
  (`run.outputs` vs `example.outputs` are easy to swap by accident).

## Mini challenge

Add a fourth example to the golden set where the expected answer is a *range*, not an
exact number, and adjust `contains_expected_number` (or add a second evaluator) to
score "close enough" instead of an exact string match.
