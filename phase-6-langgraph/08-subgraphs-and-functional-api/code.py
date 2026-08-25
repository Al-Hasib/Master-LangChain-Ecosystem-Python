"""
Phase 6 - Topic 08: Subgraphs & the Functional API

Run:
    python code.py

Demonstrates (1) a small subgraph composed into a parent graph via add_node,
and (2) the same idea as Topic 02's pipeline re-implemented with the
functional API (@entrypoint / @task) instead of StateGraph.
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
        from langgraph.checkpoint.memory import InMemorySaver
        from langgraph.func import entrypoint, task
        from langgraph.graph import StateGraph, START, END
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # === Part 1: subgraph composed into a parent graph =========================
    class OrderState(TypedDict):
        order_id: str
        in_stock: bool
        payment_ok: bool
        status: str

    def check_stock(state: OrderState) -> dict:
        return {"in_stock": True}  # simulated inventory check

    def check_payment(state: OrderState) -> dict:
        return {"payment_ok": True}  # simulated payment check

    # A small, self-contained subgraph - it knows nothing about the parent graph.
    sub_builder = StateGraph(OrderState)
    sub_builder.add_node("check_stock", check_stock)
    sub_builder.add_node("check_payment", check_payment)
    sub_builder.add_edge(START, "check_stock")
    sub_builder.add_edge("check_stock", "check_payment")
    sub_builder.add_edge("check_payment", END)
    validate_order_subgraph = sub_builder.compile()

    def process_order(state: OrderState) -> dict:
        ready = state["in_stock"] and state["payment_ok"]
        return {"status": "ready to ship" if ready else "blocked"}

    parent_builder = StateGraph(OrderState)
    # A compiled StateGraph can be passed directly as a node - same state schema,
    # no wrapper function needed.
    parent_builder.add_node("validate_order", validate_order_subgraph)
    parent_builder.add_node("process_order", process_order)
    parent_builder.add_edge(START, "validate_order")
    parent_builder.add_edge("validate_order", "process_order")
    parent_builder.add_edge("process_order", END)
    parent_graph = parent_builder.compile()

    print("--- 1) subgraph composed into a parent graph ---")
    result = parent_graph.invoke({"order_id": "ORD-1"})
    print(f"  status: {result['status']} (in_stock={result['in_stock']}, payment_ok={result['payment_ok']})\n")

    # === Part 2: functional API equivalent of Topic 02's 3-node pipeline =======
    print("--- 2) functional API (@entrypoint / @task) equivalent of Topic 02 ---")
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    @task
    def greet(topic: str) -> str:
        return f"Let's talk about {topic}."

    @task
    def call_model(greeting: str) -> str:
        prompt = f"{greeting} In one sentence, why does it matter?"
        return model.invoke(prompt).content

    @entrypoint(checkpointer=InMemorySaver())
    def pipeline(topic: str) -> str:
        # Plain Python control flow instead of nodes/edges - .result() blocks
        # for each task's return value, same checkpoint/resume guarantees as
        # a compiled StateGraph.
        greeting = greet(topic).result()
        reply = call_model(greeting).result()
        return f"{greeting}\n{reply}"

    config = {"configurable": {"thread_id": "functional-demo"}}
    final_text = pipeline.invoke("LangGraph", config)
    print(f"  {final_text}")


if __name__ == "__main__":
    main()
