"""
Phase 9 - Topic 05: Datasets & Evaluators

Builds a small golden dataset (as a plain list of dicts, and - when a LangSmith
key is present - for real in your workspace via Client.create_dataset), then
writes and exercises one custom evaluator function.

Run:
    python code.py
"""

import os
import sys
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv()

# A LangSmith dataset is just a hosted, versioned version of this list of dicts -
# each entry's "inputs" is what your app receives, "outputs" is the reference/
# expected answer to score against.
GOLDEN_SET = [
    {
        "inputs": {"question": "How many meters are in 1 kilometer?"},
        "outputs": {"answer": "1000"},
    },
    {
        "inputs": {"question": "How many grams are in 1 kilogram?"},
        "outputs": {"answer": "1000"},
    },
    {
        "inputs": {"question": "How many centimeters are in 1 meter?"},
        "outputs": {"answer": "100"},
    },
]


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def answer_question(question: str) -> str:
    """Stand-in for "your app" - the thing being evaluated. Deliberately simple
    (regex-free string math) so this file has no hidden dependency on a model
    just to demonstrate the evaluator; a real target would call an LLM/agent."""
    conversions = {"kilometer": "1000", "kilogram": "1000", "meter": "100"}
    for unit, value in conversions.items():
        if unit in question.lower():
            return f"There are {value} in it."
    return "I don't know."


def contains_expected_number(run, example) -> dict:
    """Custom evaluator: (run, example) -> {"key": ..., "score": ...}.

    This is the exact shape LangSmith's evaluate() (Topic 07) calls evaluators
    with: `run.outputs` is what your app produced, `example.outputs` is the
    dataset's reference answer. Returning a dict with "key"/"score" is what
    makes the result show up as a named, scored column in the LangSmith UI.
    """
    predicted = run.outputs.get("answer", "")
    expected = example.outputs.get("answer", "")
    return {"key": "contains_expected_number", "score": expected in predicted}


def main() -> None:
    require_openai_key()  # kept for consistency with the rest of the course; this
    # topic's core logic below needs no model call, but real evaluator work usually
    # does (Topic 06 adds an LLM-as-judge evaluator that genuinely needs it).

    print("=== Golden set (local list of dicts) ===")
    for row in GOLDEN_SET:
        print(f"  {row['inputs']} -> expected {row['outputs']}")

    print("\n=== Running the evaluator locally against each example ===")
    for row in GOLDEN_SET:
        predicted_answer = answer_question(row["inputs"]["question"])
        # Stand-ins for the real Run/Example objects evaluate() passes in Topic 07 -
        # only `.outputs` is used by this evaluator, so a lightweight namespace is
        # enough to exercise the function's actual logic here.
        fake_run = SimpleNamespace(outputs={"answer": predicted_answer})
        fake_example = SimpleNamespace(outputs=row["outputs"])
        result = contains_expected_number(fake_run, fake_example)
        print(f"  Q: {row['inputs']['question']}")
        print(f"    got: {predicted_answer!r}  ->  {result}")

    print("\n=== Creating the same dataset for real in LangSmith ===")
    if not os.getenv("LANGCHAIN_API_KEY"):
        print(
            "[skipped] LANGCHAIN_API_KEY not set - dataset creation is a hosted "
            "feature (free account at https://smith.langchain.com/).\n"
            "1) cp ../../.env.example ../../.env\n2) fill in LANGCHAIN_API_KEY\n"
            "3) re-run to create this dataset for real."
        )
        return

    try:
        from langsmith import Client
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    client = Client()
    dataset_name = "langchain-course-phase9-unit-conversion"

    # create_dataset is idempotent-ish for the demo: if it already exists from a
    # previous run, reuse it instead of erroring.
    if client.has_dataset(dataset_name=dataset_name):
        dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"Reusing existing dataset \"{dataset_name}\" ({dataset.id})")
    else:
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Phase 9 course golden set: simple unit-conversion Q&A.",
        )
        client.create_examples(dataset_id=dataset.id, examples=GOLDEN_SET)
        print(f"Created dataset \"{dataset_name}\" ({dataset.id}) with {len(GOLDEN_SET)} examples")

    project = os.getenv("LANGCHAIN_PROJECT", "langchain-ecosystem-course")
    print(f"\nGo browse it: https://smith.langchain.com/  ->  Datasets  ->  \"{dataset_name}\"")
    print(f"(traces from running against it land in project \"{project}\")")


if __name__ == "__main__":
    main()
