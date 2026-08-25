"""
Phase 7 - Topic 02: Agent Memory: Short-Term & Long-Term

Run:
    python code.py

Demonstrates: long-term memory that survives across separate, unrelated
agent.invoke() calls, using a LangGraph Store - as opposed to short-term memory
(the messages list, already covered in Phase 1 Topic 07), which resets every time.
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
        from langchain.tools import ToolRuntime, tool
        # InMemoryStore is LangGraph's key-value long-term memory store. It's the
        # verified, real API (confirmed against LangChain docs) - NOT a hand-rolled
        # stand-in. It lives only for this process's lifetime (see doc.md Production
        # notes for swapping in a persistent, DB-backed store).
        from langgraph.store.memory import InMemoryStore
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # One Store, created once, shared by every agent.invoke() call below - this is
    # what makes the memory "long-term" instead of scoped to a single conversation.
    store = InMemoryStore()
    NAMESPACE = ("demo_user", "preferences")

    @tool
    def save_preference(preference: str, runtime: ToolRuntime) -> str:
        """Save a user preference so it can be recalled in a future, separate
        conversation. `preference` should be a short description, e.g. 'metric units'.
        """
        runtime.store.put(NAMESPACE, "units", preference)
        return f"Saved preference: {preference}"

    @tool
    def get_preference(runtime: ToolRuntime) -> str:
        """Recall the user's previously saved preference, if one exists."""
        item = runtime.store.get(NAMESPACE, "units")
        return item.value if item else "No preference has been saved yet."

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[save_preference, get_preference],
        store=store,
    )

    print("--- Conversation 1 (fresh messages list) ---")
    result_1 = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "I prefer distances in metric units (km, not miles). Please remember that.",
                }
            ]
        }
    )
    print(f"  agent: {result_1['messages'][-1].content}\n")

    print("--- Conversation 2 (a completely separate invoke() - simulates a new session) ---")
    result_2 = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": "What unit system do I prefer? Use your memory tool."}
            ]
        }
    )
    print(f"  agent: {result_2['messages'][-1].content}")
    print(
        "\n(Conversation 2's messages list never mentioned units - the answer came "
        "from the Store, not from message history.)"
    )


if __name__ == "__main__":
    main()
