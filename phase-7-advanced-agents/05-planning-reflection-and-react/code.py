"""
Phase 7 - Topic 05: Planning, Reflection & ReAct

Run:
    python code.py

Demonstrates: an explicit plan-then-act step (structured output: list[str] steps)
before the agent touches any tools, and a reflection step where a second structured
call critiques the agent's draft answer once before it's finalized.
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
        from pydantic import BaseModel, Field
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    class Plan(BaseModel):
        """An ordered list of steps to solve a task."""

        steps: list[str] = Field(description="Short, ordered steps to solve the task")

    class Critique(BaseModel):
        """A self-critique of a draft answer."""

        approved: bool = Field(description="True if the draft answer is correct and complete")
        feedback: str = Field(description="Why it was approved, or what's wrong with it")
        revised_answer: str | None = Field(
            default=None, description="A corrected answer, only if approved=False"
        )

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    @tool
    def calculate(expression: str) -> str:
        """Evaluate a simple arithmetic expression, e.g. '84 * 0.15 + 5'. Digits and
        + - * / ( ) . only - no variables or function calls."""
        allowed = set("0123456789+-*/(). ")
        if not set(expression) <= allowed:
            return "Error: expression contains disallowed characters."
        try:
            return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307 - restricted charset above
        except Exception as exc:  # noqa: BLE001 - surfaced to the model as a tool error
            return f"Error: {exc}"

    task = (
        "A restaurant bill is $84. Add a 15% tip, then add a flat $5 delivery fee. "
        "What's the total, rounded to the nearest dollar?"
    )

    # --- 1) Explicit planning, BEFORE any tool is touched ---
    planner = model.with_structured_output(Plan)
    plan = planner.invoke(f"Break this task into short, ordered steps (no need to solve it yet): {task}")
    print("--- Plan ---")
    for i, step in enumerate(plan.steps, start=1):
        print(f"  {i}. {step}")

    # --- 2) Execute with the agent, feeding the plan in as guidance ---
    agent = create_agent(
        model="gpt-4o-mini",
        tools=[calculate],
        system_prompt="You are a careful math assistant. Use the calculate tool for arithmetic; don't do math in your head.",
    )
    plan_text = "\n".join(f"{i}. {s}" for i, s in enumerate(plan.steps, start=1))
    agent_input = f"{task}\n\nFollow this plan:\n{plan_text}"
    result = agent.invoke({"messages": [{"role": "user", "content": agent_input}]})
    draft_answer = result["messages"][-1].content
    print(f"\n--- Draft answer ---\n  {draft_answer}")

    # --- 3) Reflection: critique the draft once before finalizing ---
    reflector = model.with_structured_output(Critique)
    critique = reflector.invoke(
        f"Task: {task}\nDraft answer: {draft_answer}\n\n"
        "Check the arithmetic step by step. Is the draft answer correct and complete? "
        "If not, give a corrected revised_answer."
    )
    print(f"\n--- Reflection ---\n  approved: {critique.approved}\n  feedback: {critique.feedback}")

    final_answer = draft_answer if critique.approved else critique.revised_answer
    print(f"\nFinal answer: {final_answer}")


if __name__ == "__main__":
    main()
