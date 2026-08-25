"""
Phase 8 - Topic 02: LangChain vs LangGraph vs Deep Agents

Run:
    python code.py

Builds "the same" simple agent three ways to make the layering concrete: a real
create_agent() call (Phase 1), a real create_deep_agent() call (this phase), and an
illustrative-only StateGraph sketch left as a comment (Phase 6 owns real LangGraph code).
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


LANGGRAPH_SKETCH = """
# --- Illustrative only: Phase 6 owns real LangGraph code ---
# from langgraph.graph import StateGraph, MessagesState
#
# graph = StateGraph(MessagesState)
# graph.add_node("agent", call_model)          # you write call_model yourself
# graph.add_node("tools", tool_node)           # you write/route tools yourself
# graph.add_edge("agent", "tools")             # YOU wire the edges explicitly
# graph.add_conditional_edges("tools", should_continue)
# app = graph.compile()
#
# Compare to create_agent()/create_deep_agent() below: those two functions build
# a graph shaped roughly like this ONE for you. LangGraph is what you drop down to
# when you need to change the wiring itself.
""".strip()


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
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    try:
        from deepagents import create_deep_agent
    except ImportError:
        sys.exit("Missing dependency. Run: pip install deepagents")

    model = init_chat_model("gpt-4o-mini", model_provider="openai")

    @tool
    def get_capital(country: str) -> str:
        """Look up the capital city of a country."""
        capitals = {"France": "Paris", "Japan": "Tokyo", "Bangladesh": "Dhaka"}
        return capitals.get(country, "Unknown")

    question = "What's the capital of Bangladesh?"

    print("=== Layer 1: LangChain's create_agent (Phase 1) ===")
    lc_agent = create_agent(model=model, tools=[get_capital])
    lc_result = lc_agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(f"type(agent) = {type(lc_agent).__name__}")
    print(f"Answer: {lc_result['messages'][-1].content}\n")

    print("=== Layer 2: LangGraph's StateGraph (Phase 6 - illustrative only) ===")
    print(LANGGRAPH_SKETCH)
    print()

    print("=== Layer 3: Deep Agents' create_deep_agent (this phase) ===")
    deep_agent = create_deep_agent(model=model, tools=[get_capital])
    deep_result = deep_agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(f"type(agent) = {type(deep_agent).__name__}")
    print(f"Answer: {deep_result['messages'][-1].content}")
    # Both create_agent() and create_deep_agent() return the SAME kind of compiled
    # LangGraph object (a CompiledStateGraph) - confirms Deep Agents compiles down
    # to Layer 2, it doesn't bypass it.
    print(f"\nSame underlying graph type? {type(lc_agent) is type(deep_agent)}")


if __name__ == "__main__":
    main()
