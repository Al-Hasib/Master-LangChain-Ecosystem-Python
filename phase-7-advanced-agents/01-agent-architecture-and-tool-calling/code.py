"""
Phase 7 - Topic 01: Agent Architecture & Tool-Calling Agents

Run:
    python code.py

Demonstrates: reading the FULL message trace of a multi-step tool-calling run, where
the second tool call depends on the result of the first (a real dependency chain, not
two independent lookups) - the pattern every later topic in this phase builds on.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def require_keys() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def main() -> None:
    require_keys()
    try:
        from langchain.agents import create_agent
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # Fake "databases" - kept as plain dicts so the example needs no external services.
    USER_CITIES = {"Priya": "Mumbai", "Tom": "Berlin"}
    WEATHER = {"Mumbai": "32C, humid, chance of evening rain", "Berlin": "18C, overcast"}

    @tool
    def lookup_user_city(name: str) -> str:
        """Look up which city a named user lives in. Call this BEFORE get_weather
        when you only know a person's name, not their city."""
        return USER_CITIES.get(name, "unknown user")

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather forecast for a named city."""
        return WEATHER.get(city, "no forecast available")

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[lookup_user_city, get_weather],
        system_prompt=(
            "You are a helpful assistant. Use tools when they're relevant. "
            "If you need a city to look up weather but only have a person's name, "
            "look up their city first."
        ),
    )

    question = "What's the weather where Priya lives?"
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    print(f"Question: {question}\n")
    print("--- Full message trace, annotated by loop iteration ---")
    # Every AIMessage that carries tool_calls starts a new iteration of the loop
    # (model -> tools -> model -> ... -> final answer). Counting them makes the
    # "hidden" loop create_agent runs for you visible.
    iteration = 0
    for message in result["messages"]:
        kind = type(message).__name__
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            iteration += 1
            print(f"[iteration {iteration}] [{kind}] requested: {tool_calls}")
        elif kind == "ToolMessage":
            print(f"[iteration {iteration}] [{kind}] -> {message.content}")
        else:
            print(f"[{kind}] {message.content}")

    print(f"\nTotal loop iterations: {iteration}")
    print(f"Final answer: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
