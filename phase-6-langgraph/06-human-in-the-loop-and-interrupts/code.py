"""
Phase 6 - Topic 06: Human-in-the-Loop & Interrupts

Run:
    python code.py

Demonstrates a graph that pauses before a simulated "send_email" step and waits
for human approval via interrupt() / Command(resume=...) - one run approved,
one run rejected, each on its own thread_id.
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
        from langgraph.graph import StateGraph, START, END
        from langgraph.types import interrupt, Command
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    class State(TypedDict):
        topic: str
        draft: str
        approved: bool
        status: str

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    def draft_email(state: State) -> dict:
        """Runs BEFORE the pause - no side effects here that we wouldn't want
        to repeat, since a resume restarts this node's downstream sibling, not
        this one (draft_email itself only runs once, before the interrupt)."""
        prompt = f"Write a one-sentence email announcing: {state['topic']}"
        return {"draft": model.invoke(prompt).content}

    def human_approval(state: State) -> dict:
        """PAUSES the graph. Whatever is passed to Command(resume=...) on the
        next invoke() becomes the return value of interrupt() right here."""
        approved = interrupt(
            {"question": "Approve sending this email?", "draft": state["draft"]}
        )
        return {"approved": bool(approved)}

    def route_on_approval(state: State) -> str:
        return "send_email" if state["approved"] else "cancelled"

    def send_email(state: State) -> dict:
        # Simulated - a real version would call an email API here.
        return {"status": f"SENT: {state['draft']}"}

    def cancelled(state: State) -> dict:
        return {"status": "CANCELLED: no email was sent"}

    builder = StateGraph(State)
    builder.add_node("draft_email", draft_email)
    builder.add_node("human_approval", human_approval)
    builder.add_node("send_email", send_email)
    builder.add_node("cancelled", cancelled)
    builder.add_edge(START, "draft_email")
    builder.add_edge("draft_email", "human_approval")
    builder.add_conditional_edges(
        "human_approval", route_on_approval, {"send_email": "send_email", "cancelled": "cancelled"}
    )
    builder.add_edge("send_email", END)
    builder.add_edge("cancelled", END)

    # Interrupts REQUIRE a checkpointer - there'd be nowhere to save the paused
    # state otherwise.
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    def run_scenario(thread_id: str, resume_value: bool) -> None:
        config = {"configurable": {"thread_id": thread_id}}
        print(f"--- thread_id={thread_id}: run until the pause ---")
        result = graph.invoke({"topic": "our new pricing plan"}, config)

        if "__interrupt__" in result:
            payload = result["__interrupt__"][0].value
            print(f"  PAUSED - human_approval is asking: {payload['question']}")
            print(f"  draft: {payload['draft']}")
        else:
            print("  (no interrupt raised - unexpected for this graph)")
            return

        print(f"  --- resuming with Command(resume={resume_value}) ---")
        final = graph.invoke(Command(resume=resume_value), config)
        print(f"  final status: {final['status']}\n")

    run_scenario("email-approved", resume_value=True)
    run_scenario("email-rejected", resume_value=False)


if __name__ == "__main__":
    main()
