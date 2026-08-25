"""
Phase 9 - Topic 07: Experiments & Regression Testing

Runs the same small dataset through two target variants using LangSmith's
evaluate(), then compares the two experiments' pass rates as a regression check.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

DATASET_NAME = "langchain-course-phase9-topic07-regression-set"
EXAMPLES = [
    {"inputs": {"question": "kilometer"}, "outputs": {"answer": "1000"}},
    {"inputs": {"question": "kilogram"}, "outputs": {"answer": "1000"}},
    {"inputs": {"question": "meter"}, "outputs": {"answer": "100"}},
    {"inputs": {"question": "mile"}, "outputs": {"answer": "1609"}},
]


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def require_langsmith_key() -> None:
    if not os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
        sys.exit(
            "evaluate() uploads a real experiment to your LangSmith workspace, so "
            "this topic needs LangSmith on.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in LANGCHAIN_API_KEY (free account at https://smith.langchain.com/)\n"
            "3) set LANGCHAIN_TRACING_V2=true\n4) re-run"
        )


def main() -> None:
    require_openai_key()
    require_langsmith_key()
    try:
        from langsmith import Client
        from langsmith.evaluation import evaluate
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # evaluate()'s `data` argument wants a dataset name/ID (or real Example objects
    # from client.list_examples) - not arbitrary dicts - so, like Topic 05, create the
    # dataset for real (or reuse it if this script already ran once).
    client = Client()
    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"Reusing existing dataset \"{DATASET_NAME}\"")
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Phase 9 Topic 07 regression-testing example set.",
        )
        client.create_examples(dataset_id=dataset.id, examples=EXAMPLES)
        print(f"Created dataset \"{DATASET_NAME}\" with {len(EXAMPLES)} examples")

    # --- The evaluator: identical for both variants, so the comparison is fair ---
    def contains_expected_number(run, example) -> dict:
        predicted = run.outputs.get("answer", "")
        expected = example.outputs.get("answer", "")
        return {"key": "contains_expected_number", "score": expected in predicted}

    # --- Variant A: deliberately incomplete lookup table (the "old" version) ---
    def variant_a(inputs: dict) -> dict:
        table = {"kilometer": "1000", "kilogram": "1000"}  # missing meter, mile
        return {"answer": table.get(inputs["question"], "unknown")}

    # --- Variant B: complete lookup table (the "new" version) ---
    def variant_b(inputs: dict) -> dict:
        table = {"kilometer": "1000", "kilogram": "1000", "meter": "100", "mile": "1609"}
        return {"answer": table.get(inputs["question"], "unknown")}

    print("Running experiment A (variant_a)...")
    results_a = evaluate(
        variant_a,
        data=DATASET_NAME,
        evaluators=[contains_expected_number],
        experiment_prefix="phase9-topic07-variant-a",
        description="Regression baseline: incomplete unit table.",
    )

    print("Running experiment B (variant_b)...")
    results_b = evaluate(
        variant_b,
        data=DATASET_NAME,
        evaluators=[contains_expected_number],
        experiment_prefix="phase9-topic07-variant-b",
        description="Candidate change: complete unit table.",
    )

    def pass_rate(results) -> float:
        # Each row is an ExperimentResultRow dict: {"run", "example", "evaluation_results"}.
        # "evaluation_results" is itself {"results": [EvaluationResult, ...]} - our
        # evaluator returns exactly one EvaluationResult per row, hence [0].
        scores = [
            row["evaluation_results"]["results"][0].score for row in results
        ]
        return sum(bool(s) for s in scores) / len(scores)

    rate_a = pass_rate(results_a)
    rate_b = pass_rate(results_b)

    print(f"\nVariant A pass rate: {rate_a:.0%}")
    print(f"Variant B pass rate: {rate_b:.0%}")

    if rate_b < rate_a:
        print("=> REGRESSION: variant B scores worse than variant A. Do not ship.")
    elif rate_b > rate_a:
        print("=> IMPROVEMENT: variant B scores better than variant A. Safe to ship.")
    else:
        print("=> NO CHANGE in aggregate score - inspect per-example results before shipping.")

    project = os.getenv("LANGCHAIN_PROJECT", "langchain-ecosystem-course")
    print("\nBoth experiments are attached to the same dataset in LangSmith, so the UI")
    print("gives you a per-example diff, not just this aggregate number:")
    print(f"  https://smith.langchain.com/  ->  project \"{project}\"  ->  Datasets & Experiments")


if __name__ == "__main__":
    main()
