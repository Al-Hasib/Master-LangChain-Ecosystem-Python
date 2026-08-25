"""
Phase 1 - Topic 11 (Mini Project): AI Research Assistant v1

User -> LangChain Agent -> LLM -> Tools (Calculator, Web Search, Date/Time)

Run:
    python code.py
"""

import datetime
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

    # --- Tool 1: Calculator - deterministic work the model shouldn't "guess" at ---
    @tool
    def calculator(expression: str) -> str:
        """Evaluate a basic arithmetic expression, e.g. '12 * (7 + 3)'.
        Use this for ANY math instead of computing it yourself."""
        allowed = set("0123456789+-*/(). ")
        if not set(expression) <= allowed:
            return "Error: expression contains disallowed characters."
        try:
            return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307
        except Exception as exc:  # noqa: BLE001
            return f"Error evaluating expression: {exc}"

    # --- Tool 2: Web search - no API key required (DuckDuckGo) ---
    @tool
    def web_search(query: str) -> str:
        """Search the web for current information not in your training data."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "Web search unavailable: duckduckgo-search not installed."
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
        except Exception as exc:  # noqa: BLE001
            return f"Search failed (network issue?): {exc}"
        if not results:
            return "No results found."
        return "\n".join(f"- {r['title']}: {r['body'][:150]}" for r in results)

    # --- Tool 3: Date/time - models don't reliably know "today" ---
    @tool
    def current_date_time() -> str:
        """Get the current date and time. Use this whenever the user asks about
        'today', 'now', or any relative date/time."""
        return datetime.datetime.now().strftime("%A, %Y-%m-%d %H:%M")

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[calculator, web_search, current_date_time],
        system_prompt=(
            "You are a research assistant. Prefer tools over your own knowledge for: "
            "math (use calculator), current events/facts you're unsure of (use "
            "web_search), and today's date/time (use current_date_time)."
        ),
    )

    questions = [
        "What's (14 + 6) * 3?",
        "What's today's date?",
        "Search the web: what is LangGraph used for?",
    ]

    for question in questions:
        print(f"\n=== Question: {question} ===")
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        for message in result["messages"]:
            tool_calls = getattr(message, "tool_calls", None)
            if tool_calls:
                print(f"  [{type(message).__name__}] tool call(s): {tool_calls}")
        print(f"  Final answer: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
