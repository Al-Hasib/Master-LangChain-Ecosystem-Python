"""
Phase 6 - Topic 04: Checkpoints, Persistence & Threads

Run:
    python code.py

Demonstrates a checkpointed graph: the same thread_id remembers earlier turns,
a different thread_id starts with a clean slate.
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
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.graph import StateGraph, START, END, MessagesState
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    def call_model(state: MessagesState) -> dict:
        """MessagesState already accumulates messages turn over turn via its
        built-in reducer - the checkpointer is what makes that accumulation
        survive ACROSS separate .invoke() calls."""
        return {"messages": [model.invoke(state["messages"])]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", call_model)
    builder.add_edge(START, "agent")
    builder.add_edge("agent", END)

    # InMemorySaver: RAM-only checkpointer, fine for dev/demo. Swap for a durable
    # backend (e.g. PostgresSaver) in production without touching any node.
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    user_1_config = {"configurable": {"thread_id": "user-1"}}

    print("--- thread_id=user-1, turn 1 ---")
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "My name is Alice."}]},
        user_1_config,
    )
    print(f"  agent: {result['messages'][-1].content}")

    print("--- thread_id=user-1, turn 2 (same thread - should remember) ---")
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "What's my name?"}]},
        user_1_config,
    )
    print(f"  agent: {result['messages'][-1].content}")

    print("--- thread_id=user-2, turn 1 (different thread - isolated) ---")
    user_2_config = {"configurable": {"thread_id": "user-2"}}
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "What's my name?"}]},
        user_2_config,
    )
    print(f"  agent: {result['messages'][-1].content}")
    print("  (user-2 never told the graph a name - it has its own checkpoint history)")


if __name__ == "__main__":
    main()
