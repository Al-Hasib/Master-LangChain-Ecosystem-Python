"""
Phase 1 - Topic 01: What is LangChain? & Architecture

Rebuilds the tool-decision shape from Phase 0 (07-rag-vs-agent-vs-workflow) using
LangChain's init_chat_model + @tool, WITHOUT an agent runtime yet (Topic 06 adds that).
Compare this file to phase-0-foundations/07-rag-vs-agent-vs-workflow/code.py.

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

    # One line, works the same regardless of provider - Topic 02 goes deep on this.
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    @tool
    def get_weather(city: str) -> str:
        """Get the current weather for a named city."""
        fake_data = {"Dhaka": "28C, humid", "London": "14C, rainy"}
        return fake_data.get(city, "Unknown city")

    model_with_tools = model.bind_tools([get_weather])

    # Step 1: model decides whether to call the tool - compare to Phase 0's ~15 lines
    # of raw client.chat.completions.create(..., tools=[...]) for the same decision.
    response = model_with_tools.invoke([HumanMessage("What's the weather in Dhaka?")])

    if response.tool_calls:
        call = response.tool_calls[0]
        print(f"Model requested: {call['name']}({call['args']})")
        result = get_weather.invoke(call["args"])
        print(f"Tool result: {result}")
    else:
        print(f"Model answered directly: {response.content}")


if __name__ == "__main__":
    main()
