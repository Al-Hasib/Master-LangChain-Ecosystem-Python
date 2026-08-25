"""
Phase 7 - Topic 09: Agent Evaluation

Run:
    python code.py

Demonstrates: a small manual eval harness - (question, expected_tool,
expected_behavior) test cases run through an agent, checking tool-call correctness
(mechanical) and task success (LLM-as-judge, structured output), with a pass/fail
summary. No LangSmith dependency (that's Phase 9 of the course).
"""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def require_keys() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


@dataclass
class TestCase:
    question: str
    expected_tool: str
    expected_behavior: str


def main() -> None:
    require_keys()
    try:
        from langchain.agents import create_agent
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
        from pydantic import BaseModel, Field
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    @tool
    def calculate(expression: str) -> str:
        """Evaluate a simple arithmetic expression, e.g. '2 + 2'. Digits and
        + - * / ( ) . only."""
        allowed = set("0123456789+-*/(). ")
        if not set(expression) <= allowed:
            return "Error: disallowed characters."
        try:
            return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307 - restricted charset above
        except Exception as exc:  # noqa: BLE001
            return f"Error: {exc}"

    @tool
    def lookup_capital(country: str) -> str:
        """Look up the capital city of a country."""
        capitals = {"france": "Paris", "japan": "Tokyo", "brazil": "Brasilia"}
        return capitals.get(country.lower(), "Unknown country")

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[calculate, lookup_capital],
        system_prompt="You are a helpful assistant. Use tools for math and capital-city lookups.",
    )

    test_cases = [
        TestCase("What is 12 * 7?", "calculate", "The answer states the result is 84."),
        TestCase(
            "What's the capital of Japan?", "lookup_capital", "The answer states the capital is Tokyo."
        ),
        TestCase(
            "What's 15% of 200, plus 10?", "calculate", "The answer states the result is 40."
        ),
        TestCase(
            "What's the capital of Brazil?", "lookup_capital", "The answer states the capital is Brasilia."
        ),
    ]

    class Judgment(BaseModel):
        """An LLM judge's verdict on whether an answer satisfies an expected behavior."""

        passed: bool = Field(description="True if the answer satisfies the expected behavior")
        reason: str = Field(description="One short sentence justifying the verdict")

    judge_model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    judge = judge_model.with_structured_output(Judgment)

    results = []
    for case in test_cases:
        result = agent.invoke({"messages": [{"role": "user", "content": case.question}]})

        # --- Check 1: tool-call correctness (mechanical, no LLM) ---
        called_tools = set()
        for message in result["messages"]:
            for tool_call in getattr(message, "tool_calls", None) or []:
                called_tools.add(tool_call["name"])
        tool_correct = case.expected_tool in called_tools

        # --- Check 2: task success (LLM-as-judge, structured output) ---
        final_answer = result["messages"][-1].content
        judgment = judge.invoke(
            f"Question: {case.question}\n"
            f"Agent's answer: {final_answer}\n"
            f"Expected behavior: {case.expected_behavior}\n"
            "Does the agent's answer satisfy the expected behavior?"
        )

        overall_pass = tool_correct and judgment.passed
        results.append((case, called_tools, tool_correct, judgment, overall_pass))

    print("--- Eval results ---")
    for case, called_tools, tool_correct, judgment, overall_pass in results:
        status = "PASS" if overall_pass else "FAIL"
        print(f"[{status}] {case.question}")
        print(f"    expected tool: {case.expected_tool} | called tools: {called_tools} | tool_correct={tool_correct}")
        print(f"    judge: passed={judgment.passed} - {judgment.reason}")

    passed_count = sum(1 for *_r, overall_pass in results if overall_pass)
    print(f"\nSummary: {passed_count}/{len(results)} test cases passed")


if __name__ == "__main__":
    main()
