"""
Phase 1 - Topic 08: Middleware, Retries, Fallbacks & Guardrails

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
        from langchain.agents.middleware import before_model, wrap_tool_call
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # --- Guardrail: refuse to process input containing banned words ---
    @before_model
    def block_banned_words(state, runtime):
        last_message = state["messages"][-1]
        banned = ["password", "secret"]
        if any(word in str(last_message.content).lower() for word in banned):
            print("  [guardrail] blocked input containing a banned word")
            return {"jump_to": "end"}
        return None

    # --- Retry wrapper: retry a failing tool call up to 3 times ---
    @wrap_tool_call
    def retry_on_tool_error(request, handler):
        for attempt in range(1, 4):
            try:
                return handler(request)
            except RuntimeError as exc:
                print(f"  [retry] attempt {attempt} failed: {exc}")
                if attempt == 3:
                    raise

    # A tool that deliberately fails its first two calls to demonstrate the retry.
    call_count = {"n": 0}

    @tool
    def flaky_lookup(query: str) -> str:
        """Look up information for a query. May be temporarily unreliable."""
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise RuntimeError(f"simulated transient failure #{call_count['n']}")
        return f"result for '{query}': 42"

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[flaky_lookup],
        middleware=[block_banned_words, retry_on_tool_error],
    )

    print("--- 1) Guardrail blocks a banned-word input ---")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's my password reset code?"}]}
    )
    print(f"  final: {result['messages'][-1].content}\n")

    print("--- 2) Retry wrapper recovers from a flaky tool ---")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Use flaky_lookup to look up 'widgets'."}]}
    )
    print(f"  final: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
