"""
Phase 10 - Topic 09: Evaluation in CI/CD & Testing Agents

A small fixed-case test suite for tool-call correctness, written as a standalone
script (this repo's convention) rather than a pytest suite - plain assert
statements, a pass/fail summary, and a nonzero exit code on failure, which is
exactly what a CI step needs: `python code.py` as one pipeline stage.

Run:
    python code.py
"""

import sys

from dotenv import load_dotenv

load_dotenv()


def build_agent():
    from langchain.agents import create_agent
    from langchain.tools import tool

    @tool
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers together."""
        return a * b

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather for a named city."""
        return {"Paris": "18C, sunny", "London": "14C, rainy"}.get(city, "Unknown city")

    return create_agent(model="gpt-4o-mini", tools=[multiply, get_weather])


def tool_calls_from_run(agent, question: str) -> list[str]:
    """Runs the agent once and returns the list of tool names it called
    across the whole run (may be empty - that's a valid, testable outcome)."""
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    called = []
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", None) or []:
            called.append(call["name"])
    return called


# ============================================================================
# Fixed test cases: (description, question, assertion function). Each
# assertion checks a PROPERTY of the tool calls, not exact response text -
# response wording is non-deterministic; which tool got called is stable.
# ============================================================================
def case_multiply_is_called(tool_calls: list[str]) -> bool:
    return "multiply" in tool_calls


def case_weather_is_called(tool_calls: list[str]) -> bool:
    return "get_weather" in tool_calls


def case_no_tool_for_chitchat(tool_calls: list[str]) -> bool:
    return tool_calls == []


TEST_CASES = [
    ("multiply tool used for arithmetic", "What's 12 times 8?", case_multiply_is_called),
    ("weather tool used for weather", "What's the weather in Paris?", case_weather_is_called),
    ("no tool for plain chit-chat", "Hello, how are you today?", case_no_tool_for_chitchat),
]


def run_suite() -> bool:
    import os

    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run\n"
            "(These are real model calls - a CI pipeline needs this set as a secret.)"
        )

    agent = build_agent()
    results = []
    for description, question, assertion in TEST_CASES:
        tool_calls = tool_calls_from_run(agent, question)
        passed = assertion(tool_calls)
        results.append((description, passed, tool_calls))

    print("=== Agent tool-call test suite (CI gate) ===")
    all_passed = True
    for description, passed, tool_calls in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {description}  (tool_calls={tool_calls})")
        all_passed = all_passed and passed

    print(f"\n{sum(1 for _, p, _ in results if p)}/{len(results)} cases passed.")
    return all_passed


def main() -> None:
    try:
        from langchain.agents import create_agent  # noqa: F401
        from langchain.tools import tool  # noqa: F401
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    all_passed = run_suite()
    if not all_passed:
        print("\nCI GATE: FAILED - would block merge/deploy.")
        sys.exit(1)
    print("\nCI GATE: PASSED.")


if __name__ == "__main__":
    main()
