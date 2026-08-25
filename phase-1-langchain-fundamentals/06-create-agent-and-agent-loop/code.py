"""
Phase 1 - Topic 06: create_agent & the Agent Loop

Run:
    python code.py
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

    @tool
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather for a named city."""
        fake_data = {"Dhaka": "28C, humid", "London": "14C, rainy"}
        return fake_data.get(city, "Unknown city")

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[add, get_weather],
        system_prompt="You are a helpful assistant. Use tools when they're relevant.",
    )

    question = "What's 15 plus 27, and separately, what's the weather in London?"
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    print(f"Question: {question}\n")
    print("--- Full message trace (this is what create_agent automated) ---")
    for message in result["messages"]:
        kind = type(message).__name__
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            print(f"[{kind}] requested: {tool_calls}")
        else:
            print(f"[{kind}] {message.content}")

    print(f"\nFinal answer: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
