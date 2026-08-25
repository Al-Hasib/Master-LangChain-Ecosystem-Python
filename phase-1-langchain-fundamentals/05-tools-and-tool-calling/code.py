"""
Phase 1 - Topic 05: Tools & Tool Calling

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
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
        from langchain_core.messages import HumanMessage
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    @tool
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b

    @tool
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers together."""
        return a * b

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather for a named city."""
        fake_data = {"Dhaka": "28C, humid", "London": "14C, rainy"}
        return fake_data.get(city, "Unknown city")

    tools = {t.name: t for t in [add, multiply, get_weather]}
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    model_with_tools = model.bind_tools(list(tools.values()))

    question = "What's 7 times 6, and what's the weather in Dhaka?"
    response = model_with_tools.invoke([HumanMessage(question)])

    print(f"Question: {question}")
    print(f"Model requested {len(response.tool_calls)} tool call(s):\n")

    for call in response.tool_calls:
        tool_fn = tools[call["name"]]
        result = tool_fn.invoke(call["args"])
        print(f"  {call['name']}({call['args']}) -> {result}")


if __name__ == "__main__":
    main()
