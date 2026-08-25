"""
Phase 9 - Topic 03: Debugging Agents & Tool Calls

An agent with two tools, one deliberately slow AND deliberately wrong for one
input, run fully traced - demonstrates what a trace makes visible that a
terminal print() doesn't.

Run:
    python code.py
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def require_langsmith_key() -> None:
    if not os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
        sys.exit(
            "This topic is about diagnosing an agent FROM its trace, so it needs "
            "LangSmith on.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in LANGCHAIN_API_KEY (free account at https://smith.langchain.com/)\n"
            "3) set LANGCHAIN_TRACING_V2=true\n4) re-run"
        )


def main() -> None:
    require_openai_key()
    require_langsmith_key()
    try:
        from langchain.agents import create_agent
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    @tool
    def unit_price(item: str) -> str:
        """Look up the unit price for a named item."""
        prices = {"widget": "$4.50", "gadget": "$12.00"}
        return prices.get(item.lower(), "Unknown item")

    @tool
    def flaky_shipping_estimate(item: str) -> str:
        """Look up the shipping estimate (in days) for a named item.

        Deliberately buggy for the demo:
        - always slow (simulates an unoptimized downstream API call)
        - silently WRONG for "gadget" (simulates a real data bug), so you can
          see a trace surface a bug that a quick glance at the final answer wouldn't
        """
        time.sleep(2)  # <- shows up as a fat, easy-to-spot latency bar in the trace
        if item.lower() == "gadget":
            return "2 days"  # WRONG on purpose - real data says 9 days
        estimates = {"widget": "3 days"}
        return estimates.get(item.lower(), "Unknown item")

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[unit_price, flaky_shipping_estimate],
        system_prompt=(
            "You are a helpful shopping assistant. Use tools to answer questions "
            "about price and shipping. Always report the tool's exact numbers."
        ),
    )

    question = "What's the price and shipping time for a gadget?"
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    print(f"Question: {question}\n")
    print("--- Full message trace (what you'd ALSO see, per-node, in LangSmith) ---")
    for message in result["messages"]:
        kind = type(message).__name__
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            print(f"[{kind}] requested: {tool_calls}")
        else:
            print(f"[{kind}] {message.content}")

    print(f"\nFinal answer: {result['messages'][-1].content}")
    print(
        "\nNotice the final answer repeats \"2 days\" for gadget shipping - that's "
        "wrong (should be 9). In the terminal, that bug is invisible unless you "
        "already know the real number. In the LangSmith trace, open the "
        "flaky_shipping_estimate child run: its OUTPUT literally says \"2 days\" for "
        "input \"gadget\" - the bug is caught by inspecting the tool's own run, before "
        "you even have to reason about whether the final answer is right. You'd also "
        "immediately see that child run's ~2s latency bar dwarfing every other step."
    )

    project = os.getenv("LANGCHAIN_PROJECT", "langchain-ecosystem-course")
    print("\nGo look at the real trace:")
    print(f"  https://smith.langchain.com/  ->  project \"{project}\"  ->  latest run")
    print("  -> expand \"flaky_shipping_estimate\" -> compare its output to reality")


if __name__ == "__main__":
    main()
