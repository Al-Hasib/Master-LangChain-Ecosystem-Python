"""
Capstone 04: Deep Research Agent

Run:
    python code.py

Demonstrates: a structured-output planner (Phase 8 Topic 03) that breaks a research
topic into ordered steps, a delegation loop handing each step to either a focused
web-search sub-agent (Phase 8 Topic 05) or a note-taking step, an in-memory scratchpad
standing in for a deep agent's filesystem tool (Phase 8 Topic 04), and a final
structured synthesis.
"""

import os
import sys
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    sys.exit(
        "Missing OPENAI_API_KEY.\n1) cp ../.env.example ../.env\n"
        "2) fill in your key\n3) re-run"
    )

try:
    from langchain.agents import create_agent
    from langchain.chat_models import init_chat_model
    from langchain.tools import tool
    from pydantic import BaseModel, Field
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r ../requirements.txt")


class PlanStep(BaseModel):
    description: str = Field(description="What this step should accomplish.")
    step_type: Literal["web_search", "note"] = Field(
        description="'web_search' delegates to a research sub-agent with web access. "
        "'note' summarizes findings gathered so far - use it after a couple of "
        "web_search steps to consolidate before moving on."
    )


class ResearchPlan(BaseModel):
    topic: str
    steps: list[PlanStep] = Field(description="3-6 ordered steps.")


class ResearchReport(BaseModel):
    title: str
    summary: str = Field(description="2-3 sentence executive summary.")
    findings: list[str] = Field(description="3-6 concrete findings pulled from the scratchpad.")
    sources: list[str] = Field(description="Source titles/URLs mentioned in the scratchpad, if any.")
    recommendation: str = Field(description="One concrete takeaway or next step.")


def make_web_search_tool():
    @tool
    def web_search(query: str) -> str:
        """Search the web for information relevant to the current research step."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "Web search unavailable: duckduckgo-search not installed."
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
        except Exception as exc:  # noqa: BLE001
            return f"Search failed (network issue?): {exc}"
        if not results:
            return "No results found."
        return "\n".join(f"- {r['title']} ({r['href']}): {r['body'][:150]}" for r in results)

    return web_search


def build_plan(model, topic: str) -> ResearchPlan:
    planner = model.with_structured_output(ResearchPlan)
    return planner.invoke(
        f"Create a research plan for this topic: {topic!r}\n"
        "Produce 3-6 ordered steps. Use 'web_search' steps to gather information and "
        "an occasional 'note' step to consolidate findings gathered so far. The last "
        "step should typically be a 'note' step."
    )


def run_web_search_step(model, web_search_tool, step: PlanStep, scratchpad: list[str]) -> str:
    """A focused, isolated sub-agent - it only sees this one step's description, not
    the whole run's history, which is the point: contained context per sub-task
    (Phase 8 Topic 05) instead of one sprawling conversation."""
    sub_agent = create_agent(
        model=model,
        tools=[web_search_tool],
        system_prompt=(
            "You are a focused research sub-agent. Use web_search to investigate "
            "the assigned step, then report your finding in 2-4 sentences with a "
            "source if available."
        ),
    )
    result = sub_agent.invoke({"messages": [{"role": "user", "content": step.description}]})
    finding = result["messages"][-1].content
    entry = f"[web_search] {step.description} -> {finding}"
    scratchpad.append(entry)
    return entry


def run_note_step(model, step: PlanStep, scratchpad: list[str]) -> str:
    """Consolidates the scratchpad so far into one note, appended back onto the
    scratchpad - standing in for a deep agent writing a summary file to disk."""
    context = "\n".join(scratchpad) if scratchpad else "(nothing gathered yet)"
    note = model.invoke(
        f"Research notes so far:\n{context}\n\n"
        f"Task: {step.description}\n"
        "Write a short consolidated note (2-4 sentences) summarizing the key points "
        "from the notes above."
    ).content
    entry = f"[note] {note}"
    scratchpad.append(entry)
    return entry


def synthesize(model, topic: str, scratchpad: list[str]) -> ResearchReport:
    synthesizer = model.with_structured_output(ResearchReport)
    full_scratchpad = "\n".join(scratchpad)
    return synthesizer.invoke(
        f"Research topic: {topic}\n\nFull scratchpad of findings and notes:\n"
        f"{full_scratchpad}\n\nWrite a final structured research report from this."
    )


def main() -> None:
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    web_search_tool = make_web_search_tool()

    topic = "The current state of AI agent frameworks for enterprise use in 2026"
    print(f"Research topic: {topic}\n")

    plan = build_plan(model, topic)
    print("Plan:")
    for i, step in enumerate(plan.steps, start=1):
        print(f"  {i}. [{step.step_type}] {step.description}")
    print()

    scratchpad: list[str] = []
    for i, step in enumerate(plan.steps, start=1):
        print(f"=== Step {i}/{len(plan.steps)}: [{step.step_type}] {step.description} ===")
        if step.step_type == "web_search":
            entry = run_web_search_step(model, web_search_tool, step, scratchpad)
        else:
            entry = run_note_step(model, step, scratchpad)
        print(f"  {entry}\n")

    print("=== Final synthesis ===")
    report = synthesize(model, topic, scratchpad)
    print(f"Title: {report.title}")
    print(f"Summary: {report.summary}")
    print("Findings:")
    for finding in report.findings:
        print(f"  - {finding}")
    print("Sources:")
    for source in report.sources:
        print(f"  - {source}")
    print(f"Recommendation: {report.recommendation}")


if __name__ == "__main__":
    main()
