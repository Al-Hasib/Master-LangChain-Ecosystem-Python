"""
Phase 6 - Topic 03: StateGraph & Conditional Edges

Run:
    python code.py

Demonstrates a classify-then-route graph: one LLM node picks a category, and
add_conditional_edges sends state down one of three branches based on it.
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
        from typing_extensions import TypedDict

        from langchain.chat_models import init_chat_model
        from langgraph.graph import StateGraph, START, END
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    class State(TypedDict):
        message: str
        category: str
        response: str

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    VALID_CATEGORIES = ("billing", "technical", "general")

    def classify(state: State) -> dict:
        """The only job of this node: read the message, pick ONE category word."""
        prompt = (
            "Classify this support message into exactly one word - "
            f"billing, technical, or general. Message: {state['message']!r}\n"
            "Reply with only the single category word."
        )
        raw = model.invoke(prompt).content.strip().lower()
        category = raw if raw in VALID_CATEGORIES else "general"  # safe fallback
        return {"category": category}

    def route_by_category(state: State) -> str:
        """The router: reads state, returns a key - does NO other work."""
        return state["category"]

    def billing_node(state: State) -> dict:
        return {"response": "Routed to billing: checking your invoice history."}

    def technical_node(state: State) -> dict:
        return {"response": "Routed to technical: pulling up troubleshooting steps."}

    def general_node(state: State) -> dict:
        return {"response": "Routed to general: happy to help - could you say more?"}

    builder = StateGraph(State)
    builder.add_node("classify", classify)
    builder.add_node("billing_node", billing_node)
    builder.add_node("technical_node", technical_node)
    builder.add_node("general_node", general_node)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify",
        route_by_category,
        {
            "billing": "billing_node",
            "technical": "technical_node",
            "general": "general_node",
        },
    )
    # Every branch still needs its own way to END - conditional edges only pick
    # ONE path, they don't merge the branches back together automatically.
    builder.add_edge("billing_node", END)
    builder.add_edge("technical_node", END)
    builder.add_edge("general_node", END)

    graph = builder.compile()

    messages = [
        "I was charged twice for my subscription this month.",
        "The app crashes every time I try to export a PDF.",
        "What are your support hours?",
    ]

    for message in messages:
        result = graph.invoke({"message": message})
        print(f"message:  {message}")
        print(f"category: {result['category']}")
        print(f"response: {result['response']}\n")


if __name__ == "__main__":
    main()
