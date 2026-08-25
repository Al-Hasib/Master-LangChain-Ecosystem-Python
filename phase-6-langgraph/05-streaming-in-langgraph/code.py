"""
Phase 6 - Topic 05: Streaming in LangGraph

Run:
    python code.py

Demonstrates graph.stream() with two stream_mode values on the same classify-
then-route graph from Topic 03: "updates" (per-node deltas) and "values" (full
accumulated state after each node).
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
        prompt = (
            "Classify this support message into exactly one word - "
            f"billing, technical, or general. Message: {state['message']!r}\n"
            "Reply with only the single category word."
        )
        raw = model.invoke(prompt).content.strip().lower()
        category = raw if raw in VALID_CATEGORIES else "general"
        return {"category": category}

    def route_by_category(state: State) -> str:
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
    builder.add_edge("billing_node", END)
    builder.add_edge("technical_node", END)
    builder.add_edge("general_node", END)
    graph = builder.compile()

    question = {"message": "I was charged twice for my subscription this month."}

    print('--- stream_mode="updates" (only what each node changed) ---')
    for chunk in graph.stream(question, stream_mode="updates"):
        for node_name, node_output in chunk.items():
            print(f"  [{node_name}] {node_output}")

    print('\n--- stream_mode="values" (full accumulated state after each node) ---')
    for chunk in graph.stream(question, stream_mode="values"):
        print(f"  {chunk}")


if __name__ == "__main__":
    main()
