"""
Phase 7 - Topic 06: Multi-Agent Systems Overview

Run:
    python code.py

Demonstrates: the smallest possible multi-agent system - two separately-specialized
agents (a research agent, a writer agent), with one explicit handoff between them.
The full router/supervisor/handoff toolkit is in Topic 07.
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
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # A fake search tool so the research agent has something to call - keeps the demo
    # free of real network calls while still exercising a real tool-calling loop.
    FAKE_SEARCH_RESULTS = {
        "langgraph": [
            "LangGraph is a low-level orchestration framework for building stateful, multi-actor apps.",
            "It represents workflows as graphs of nodes and edges, with explicit state.",
            "It underpins create_agent's loop and adds durable execution, streaming, and human-in-the-loop.",
        ]
    }

    @tool
    def web_search(query: str) -> str:
        """Search the web for a topic and return a few short facts."""
        key = next((k for k in FAKE_SEARCH_RESULTS if k in query.lower()), None)
        facts = FAKE_SEARCH_RESULTS.get(key, ["No results found."])
        return "\n".join(f"- {fact}" for fact in facts)

    # --- Agent 1: research - narrow job, one tool, no writing responsibility ---
    research_agent = create_agent(
        model="gpt-4o-mini",
        tools=[web_search],
        system_prompt=(
            "You are a research assistant. Use web_search to gather facts about the "
            "user's topic. Reply with a terse bullet list of raw facts only - no prose, "
            "no summary, no conclusions. That's another agent's job."
        ),
    )

    # --- Agent 2: writer - no tools at all, only turns facts into prose ---
    writer_agent = create_agent(
        model="gpt-4o-mini",
        tools=[],
        system_prompt=(
            "You are a writer. You'll be given raw research facts. Turn them into one "
            "polished, friendly paragraph for a general audience. Do not invent facts "
            "that weren't given to you."
        ),
    )

    topic = "LangGraph"
    print(f"--- Step 1: research_agent gathers facts about '{topic}' ---")
    research_result = research_agent.invoke(
        {"messages": [{"role": "user", "content": f"Research: {topic}"}]}
    )
    raw_facts = research_result["messages"][-1].content
    print(raw_facts)

    print("\n--- Step 2: EXPLICIT HANDOFF - raw_facts becomes the writer's input ---")
    writer_result = writer_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Write a paragraph about {topic} using only these facts:\n{raw_facts}",
                }
            ]
        }
    )
    print(writer_result["messages"][-1].content)


if __name__ == "__main__":
    main()
