# 07 — Experiments & Regression Testing

## Problem

You changed a prompt (Topic 04) or swapped a model. Did it actually get better, or does
it just *feel* better because you tried three questions by hand and they looked fine?
Without running both versions against the same fixed set of questions and comparing
scores, "it feels better" is not evidence — and worse, you have no way to catch a
regression (a change that quietly makes some other case worse) before it ships.

## Concept

An **experiment** in LangSmith is one full run of a target function (your app, a chain,
an agent) over every example in a dataset, scored by one or more evaluators (Topic 05) —
exactly the mechanics from Topics 05–06, wired together by `evaluate()`:

```python
from langsmith.evaluation import evaluate

def target(inputs: dict) -> dict:
    return {"answer": my_app(inputs["question"])}

results = evaluate(
    target,
    data="phase9-golden-set",       # a dataset name/ID, or an iterable of real
    evaluators=[contains_expected_number],   # Example objects from client.list_examples()
    experiment_prefix="prompt-v2",
)
```

(`data` does **not** accept a raw list of plain `{"inputs": ..., "outputs": ...}` dicts —
those need to become a real dataset first, via `create_dataset`/`create_examples`
(Topic 05), same as any other dataset.)

Regression testing is just running `evaluate()` **twice** — once per variant (old
prompt/model vs. new) — over the *same* dataset, then comparing the aggregate scores:

```text
                    ┌──────────────┐
   dataset  ───────►│  variant A   │───► experiment A ───► score_A
   (same examples,  │ (old prompt) │
    every run)       └──────────────┘
                    ┌──────────────┐
   dataset  ───────►│  variant B   │───► experiment B ───► score_B
                     │ (new prompt) │
                     └──────────────┘

                     score_B < score_A  ->  REGRESSION, don't ship
                     score_B >= score_A ->  safe to ship
```

Each `evaluate()` call creates a separate, named **experiment** tied to the same dataset
in LangSmith, so in the web app you get a diff view across experiments for free — not
just the final aggregate number, but which *specific* examples flipped from pass to fail.

## Minimal code

`code.py` defines two target variants that answer the Topic 05 unit-conversion questions
differently (`variant_a`: a deliberately incomplete lookup table; `variant_b`: a more
complete one), runs `evaluate()` for each over the same small dataset with the Topic 05
evaluator, and prints a pass-rate comparison — a manual regression check computed from
real `evaluate()` results, the same idea LangSmith's UI shows as a diff.

## Production notes

- Run regression tests as a CI step before merging any prompt/model change — treat the
  golden dataset like a test suite, not an occasional manual check.
- Use `experiment_prefix` consistently (`"prod-model=gpt-4o-mini"`) so experiments are
  identifiable months later without opening each one to check its config.
- Track `summary_evaluators` (Topic 05's `precision` example) for metrics that only make
  sense in aggregate (precision/recall), separately from per-example evaluators.

## Debugging

- Two experiments show wildly different scores despite an "unrelated" change → check
  `data=` actually passed the *same* dataset/example set both times — a filtered/reduced
  example list is an easy way to accidentally invalidate a comparison.
- `evaluate()` looks like it hangs → check `max_concurrency`; a too-low value on a large
  dataset with slow evaluators (LLM judges) is just slow, not broken.
- Aggregate score improves but a specific important example regressed → this is exactly
  why you compare per-example, not just the aggregate — an average can hide a real
  regression on your most important case.

## Mini challenge

Add a third variant that's deliberately worse than both A and B, run all three through
`evaluate()`, and confirm your comparison logic correctly flags it as a regression
against variant B (not just against variant A).
