"""
Phase 6 - Topic 01: Why LangGraph? (LangChain vs LangGraph)

Run:
    python code.py

Demonstrates the same "ask a question that needs one tool call" task solved two
ways: create_agent (Phase 1's opaque loop) and a hand-built LangGraph StateGraph
(the same loop, drawn explicitly) - to make "same idea, more control" concrete.
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
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
        from langgraph.graph import StateGraph, START, MessagesState
        from langgraph.prebuilt import ToolNode, tools_condition
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    @tool
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b

    question = "What's 15 plus 27?"

    # --- Version 1: create_agent (Phase 1 Topic 06) - the loop is hidden ---
    print("--- 1) create_agent (opaque loop) ---")
    agent = create_agent(
        model="gpt-4o-mini",
        tools=[add],
        system_prompt="You are a helpful assistant. Use tools when relevant.",
    )
    agent_result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(f"  final: {agent_result['messages'][-1].content}\n")

    # --- Version 2: the SAME loop, hand-built as a LangGraph StateGraph ---
    print("--- 2) hand-built StateGraph (same loop, every wire is yours) ---")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    model_with_tools = model.bind_tools([add])

    def call_model(state: MessagesState) -> dict:
        """The 'agent' node: call the model with the running message list."""
        return {"messages": [model_with_tools.invoke(state["messages"])]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode([add]))
    builder.add_edge(START, "agent")
    # tools_condition inspects the last message: tool_calls present -> "tools",
    # otherwise -> END. This IS what create_agent does for you under the hood.
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")  # loop back after running a tool
    graph = builder.compile()

    graph_result = graph.invoke({"messages": [{"role": "user", "content": question}]})
    print(f"  final: {graph_result['messages'][-1].content}")

    print("\nBoth answers come from the exact same request -> tool -> feed-back loop -")
    print("one hidden inside create_agent, one drawn explicitly as a graph.")


if __name__ == "__main__":
    main()
