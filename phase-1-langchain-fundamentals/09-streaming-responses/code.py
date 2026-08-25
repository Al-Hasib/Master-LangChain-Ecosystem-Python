"""
Phase 1 - Topic 09: Streaming Responses

Run:
    python code.py
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()


def require_keys() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def stream_model_tokens(model) -> None:
    print("--- 1) Token streaming from a single model call ---")
    start = time.perf_counter()
    first_token_at = None
    for chunk in model.stream("In two sentences, explain what a closure is in Python."):
        if first_token_at is None and chunk.text:
            first_token_at = time.perf_counter() - start
        print(chunk.text, end="", flush=True)
    total = time.perf_counter() - start
    print(f"\n\n  time-to-first-token: {first_token_at:.2f}s | total: {total:.2f}s")


def stream_agent_steps(agent) -> None:
    print("\n--- 2) Agent step streaming (stream_mode='updates') ---")
    question = "What's 8 times 9, then what's the weather in London?"
    for step in agent.stream(
        {"messages": [{"role": "user", "content": question}]}, stream_mode="updates"
    ):
        for node_name, node_output in step.items():
            messages = node_output.get("messages", [])
            for message in messages:
                tool_calls = getattr(message, "tool_calls", None)
                if tool_calls:
                    print(f"  [{node_name}] requested tool call(s): {tool_calls}")
                else:
                    print(f"  [{node_name}] {message.content}")


def main() -> None:
    require_keys()
    try:
        from langchain.agents import create_agent
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    stream_model_tokens(model)

    @tool
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers together."""
        return a * b

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather for a named city."""
        return {"London": "14C, rainy"}.get(city, "Unknown city")

    agent = create_agent(model="gpt-4o-mini", tools=[multiply, get_weather])
    stream_agent_steps(agent)


if __name__ == "__main__":
    main()
