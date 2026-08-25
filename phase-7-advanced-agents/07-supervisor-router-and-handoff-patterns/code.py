"""
Phase 7 - Topic 07: Supervisor, Router & Handoff Patterns

Run:
    python code.py

Demonstrates the three standard multi-agent topologies:
  (a) Router     - classify, then dispatch to exactly one specialist agent.
  (b) Supervisor - the PHASE 7 PROJECT (Multi-Agent Research System): a coordinating
                   agent that calls other agents AS TOOLS.
  (c) Handoff    - one agent explicitly returns control to another mid-conversation.

All hand-rolled with plain create_agent + @tool - no third-party supervisor package.
"""

import os
import sys
from typing import Literal

from dotenv import load_dotenv

load_dotenv()


def require_keys() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def section_router(create_agent, init_chat_model, BaseModel, Field) -> None:
    print("=" * 70)
    print("(a) ROUTER - classify, then dispatch to one specialist")
    print("=" * 70)

    class Category(BaseModel):
        """Which team should handle this request."""

        name: Literal["billing", "technical"] = Field(description="The best-fit team")

    router_model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    classifier = router_model.with_structured_output(Category)

    billing_agent = create_agent(
        model="gpt-4o-mini", tools=[], system_prompt="You are a billing support specialist. Be concise."
    )
    technical_agent = create_agent(
        model="gpt-4o-mini", tools=[], system_prompt="You are a technical support specialist. Be concise."
    )

    request = "I was charged twice for my subscription this month - can I get a refund?"
    category = classifier.invoke(f"Classify this support request: {request}")
    print(f"  classified as: {category.name}")

    specialist = billing_agent if category.name == "billing" else technical_agent
    result = specialist.invoke({"messages": [{"role": "user", "content": request}]})
    print(f"  [{category.name} agent] {result['messages'][-1].content}\n")


def section_supervisor(create_agent, tool) -> None:
    print("=" * 70)
    print("(b) SUPERVISOR - Phase 7 project: Multi-Agent Research System")
    print("=" * 70)

    # Small fake "data sources" so the demo needs no external services.
    FACTS = {
        "langgraph": [
            "LangGraph is a low-level orchestration framework for stateful, multi-actor LLM apps.",
            "It models workflows as an explicit graph of nodes and edges over shared state.",
        ]
    }
    STATS = {
        "langgraph": "GitHub stars: 10k+ | first released: Jan 2024 | primary language: Python",
    }

    @tool
    def fake_search(query: str) -> str:
        """Search for qualitative facts about a topic."""
        key = next((k for k in FACTS if k in query.lower()), None)
        return "\n".join(f"- {f}" for f in FACTS.get(key, ["No results found."]))

    @tool
    def fake_stats_lookup(query: str) -> str:
        """Look up quantitative stats/numbers about a topic."""
        key = next((k for k in STATS if k in query.lower()), None)
        return STATS.get(key, "No stats found.")

    research_agent = create_agent(
        model="gpt-4o-mini",
        tools=[fake_search],
        system_prompt="You are a research agent. Use fake_search to gather qualitative facts. Reply as a terse bullet list.",
    )
    data_agent = create_agent(
        model="gpt-4o-mini",
        tools=[fake_stats_lookup],
        system_prompt="You are a data agent. Use fake_stats_lookup to gather quantitative stats. Reply as a terse bullet list.",
    )
    analyst_agent = create_agent(
        model="gpt-4o-mini",
        tools=[],
        system_prompt="You are an analyst. Given research notes and data notes, synthesize 2-3 key insights.",
    )
    writer_agent = create_agent(
        model="gpt-4o-mini",
        tools=[],
        system_prompt="You are a writer. Turn the given insights into a short, polished report (3-4 sentences).",
    )

    # Each specialist is exposed to the supervisor as an ordinary tool - the
    # supervisor never sees the sub-agents' internal message loops, only the
    # string each one returns. This is the "agents as tools" supervisor pattern.
    @tool
    def research_tool(topic: str) -> str:
        """Delegate to the Research Agent: gather qualitative facts about a topic."""
        result = research_agent.invoke({"messages": [{"role": "user", "content": f"Research: {topic}"}]})
        return result["messages"][-1].content

    @tool
    def data_tool(topic: str) -> str:
        """Delegate to the Data Agent: gather quantitative stats/numbers about a topic."""
        result = data_agent.invoke({"messages": [{"role": "user", "content": f"Get stats on: {topic}"}]})
        return result["messages"][-1].content

    @tool
    def analyst_tool(notes: str) -> str:
        """Delegate to the Analyst Agent: synthesize combined research+data notes into key insights."""
        result = analyst_agent.invoke({"messages": [{"role": "user", "content": notes}]})
        return result["messages"][-1].content

    @tool
    def writer_tool(insights: str) -> str:
        """Delegate to the Writer Agent: turn insights into the final polished report."""
        result = writer_agent.invoke({"messages": [{"role": "user", "content": insights}]})
        return result["messages"][-1].content

    supervisor = create_agent(
        model="gpt-4o-mini",
        tools=[research_tool, data_tool, analyst_tool, writer_tool],
        system_prompt=(
            "You are a supervisor coordinating four specialist agents to produce a research "
            "report. Follow this exact sequence: "
            "1) call research_tool with the topic, "
            "2) call data_tool with the topic, "
            "3) call analyst_tool with both results combined as one string, "
            "4) call writer_tool with the insights from step 3. "
            "Return the writer_tool's report as your final answer, verbatim - do not "
            "rewrite it yourself."
        ),
    )

    topic = "LangGraph"
    result = supervisor.invoke(
        {"messages": [{"role": "user", "content": f"Produce a short research report on: {topic}"}]}
    )

    print("  --- Supervisor's tool-call trace ---")
    for message in result["messages"]:
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            print(f"    -> called: {[tc['name'] for tc in tool_calls]}")
    print(f"\n  Final report:\n  {result['messages'][-1].content}\n")


def section_handoff(create_agent, tool) -> None:
    print("=" * 70)
    print("(c) HANDOFF - one agent explicitly returns control to another")
    print("=" * 70)

    @tool
    def handoff_to_billing(summary: str) -> str:
        """Call this when the user's request is about billing, payments, or refunds -
        you are NOT equipped to resolve those yourself. Pass a short summary of what
        the user needs so the billing team has full context."""
        return f"[handoff-requested] {summary}"

    general_agent = create_agent(
        model="gpt-4o-mini",
        tools=[handoff_to_billing],
        system_prompt=(
            "You handle general product questions. If the request is about billing, "
            "payments, or refunds, call handoff_to_billing instead of answering it yourself."
        ),
    )
    billing_agent = create_agent(
        model="gpt-4o-mini", tools=[], system_prompt="You are a billing specialist. Resolve the request concisely."
    )

    request = "I was charged twice for my subscription, can you refund the extra charge?"
    result = general_agent.invoke({"messages": [{"role": "user", "content": request}]})

    handoff_summary = None
    for message in result["messages"]:
        if type(message).__name__ == "ToolMessage" and getattr(message, "name", "") == "handoff_to_billing":
            # The tool's return value carries the summary the general agent extracted.
            handoff_summary = message.content.removeprefix("[handoff-requested] ")

    if handoff_summary:
        print(f"  [orchestrator] general_agent handed off: {handoff_summary}")
        final = billing_agent.invoke({"messages": [{"role": "user", "content": handoff_summary}]})
        print(f"  [billing_agent] {final['messages'][-1].content}")
    else:
        print(f"  [general_agent] {result['messages'][-1].content}")


def main() -> None:
    require_keys()
    try:
        from langchain.agents import create_agent
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
        from pydantic import BaseModel, Field
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    section_router(create_agent, init_chat_model, BaseModel, Field)
    section_supervisor(create_agent, tool)
    section_handoff(create_agent, tool)


if __name__ == "__main__":
    main()
