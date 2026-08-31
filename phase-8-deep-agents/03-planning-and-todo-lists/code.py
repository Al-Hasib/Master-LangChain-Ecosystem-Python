"""
Phase 8 - Topic 03: Planning & Todo Lists

Run:
    python code.py

Confirmed API: task planning is opt-in in deepagents 0.7+ via TodoListMiddleware
(imported from langchain.agents.middleware, not deepagents itself). See
https://docs.langchain.com/oss/python/deepagents/middleware
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
        from langchain.agents.middleware import TodoListMiddleware
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    try:
        from deepagents import create_deep_agent
    except ImportError:
        sys.exit("Missing dependency. Run: pip install deepagents")

    model = init_chat_model("gpt-4o-mini", model_provider="openai")

    # Two intentionally tiny "research" tools - the point of this topic is the
    # planning tool, not the tools themselves.
    @tool
    def lookup_fact(topic: str) -> str:
        """Look up one fact about a topic from a small offline reference."""
        facts = {
            "pinecone": "Pinecone is a managed, cloud-native vector database.",
            "faiss": "FAISS is Meta's library for fast similarity search.",
            "qdrant": "Qdrant is a vector database with strong filtering support.",
        }
        return facts.get(topic.lower(), f"No fact on file for '{topic}'.")

    agent = create_deep_agent(
        model=model,
        tools=[lookup_fact],
        system_prompt=(
            "You are a research assistant. For any multi-step task, write and "
            "maintain a todo list with write_todos before and while you work."
        ),
        # write_todos is OPT-IN as of deepagents 0.7 - this is the one line that
        # turns it on. Without it, no planning tool is bound at all.
        middleware=[TodoListMiddleware()],
    )

    question = (
        "Look up facts about pinecone, faiss, and qdrant, then write a one-sentence "
        "comparison of the three."
    )
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    print("--- write_todos calls seen during the run ---")
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", []) or []:
            if call["name"] == "write_todos":
                print(f"  {call['args']}")

    print("\n--- Final todo list state (result['todos']) ---")
    for todo in result.get("todos", []):
        print(f"  [{todo.get('status')}] {todo.get('content')}")

    print(f"\nFinal answer: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
