"""
Phase 6 - Topic 02: Graphs, Nodes, Edges & State

Run:
    python code.py

Demonstrates the smallest useful LangGraph shape: a 3-node sequential pipeline
(greet -> call_model -> format_output) wired with plain add_edge calls, so the
state/node/edge mental model is visible before any branching is introduced.
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

    # The state schema: every node reads some of these keys and returns updates
    # to some of these keys. Nothing outside this shape can flow through the graph.
    class State(TypedDict):
        topic: str
        greeting: str
        reply: str
        final: str

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    def greet(state: State) -> dict:
        """Deterministic node: no model call, just builds an opening line."""
        return {"greeting": f"Let's talk about {state['topic']}."}

    def call_model(state: State) -> dict:
        """LLM node: asks the model one short question about the topic."""
        prompt = f"{state['greeting']} In one sentence, why does it matter?"
        response = model.invoke(prompt)
        return {"reply": response.content}

    def format_output(state: State) -> dict:
        """Deterministic node: combines everything earlier nodes produced."""
        combined = f"{state['greeting']}\n{state['reply']}"
        return {"final": combined}

    builder = StateGraph(State)
    builder.add_node("greet", greet)
    builder.add_node("call_model", call_model)
    builder.add_node("format_output", format_output)

    # Plain, deterministic wiring - always this order, no branching (see Topic 03).
    builder.add_edge(START, "greet")
    builder.add_edge("greet", "call_model")
    builder.add_edge("call_model", "format_output")
    builder.add_edge("format_output", END)

    graph = builder.compile()

    result = graph.invoke({"topic": "LangGraph"})

    print("--- Final merged state (every node's contribution) ---")
    for key, value in result.items():
        print(f"  {key}: {value}")

    print(f"\n--- Formatted output ---\n{result['final']}")


if __name__ == "__main__":
    main()
