"""
Phase 6 - Topic 10 (Project): Customer Support Workflow

Run:
    python code.py

Combines Topics 02-06 into one graph: classify -> route -> specialized agent
-> human approval (interrupt) -> respond. Runs one approved ticket and one
rejected ticket, each on its own thread_id.
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
        ticket: str
        category: str
        draft: str
        approved: bool
        final_response: str

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    VALID_CATEGORIES = ("billing", "technical", "general")

    # --- classify (Topic 03) ---
    def classify(state: State) -> dict:
        raw = model.invoke(
            "Classify this support ticket into exactly one word - billing, "
            f"technical, or general: {state['ticket']!r}\nReply with only the word."
        ).content.strip().lower()
        return {"category": raw if raw in VALID_CATEGORIES else "general"}

    def route_by_category(state: State) -> str:
        return state["category"]

    # --- specialized agent nodes (Topic 02's call_model, one per branch) ---
    def make_agent_node(role_description: str):
        def agent_node(state: State) -> dict:
            prompt = (
                f"You are a {role_description}. Write a short, friendly draft reply "
                f"to this customer ticket: {state['ticket']!r}"
            )
            return {"draft": model.invoke(prompt).content}

        return agent_node

    billing_agent = make_agent_node("billing support specialist")
    technical_agent = make_agent_node("technical support specialist")
    general_agent = make_agent_node("general customer support representative")

    # --- human_approval (Topic 06) ---
    def human_approval(state: State) -> dict:
        approved = interrupt(
            {"question": "Approve this draft reply?", "draft": state["draft"]}
        )
        return {"approved": bool(approved)}

    def route_on_approval(state: State) -> str:
        return "respond"  # both approved and rejected paths go to the same node;
        # respond() below branches on state["approved"] to decide the message.

    # --- respond (final deterministic node) ---
    def respond(state: State) -> dict:
        if state["approved"]:
            return {"final_response": f"SENT: {state['draft']}"}
        return {"final_response": "ESCALATED: draft was rejected, routing to a human agent"}

    builder = StateGraph(State)
    builder.add_node("classify", classify)
    builder.add_node("billing_agent", billing_agent)
    builder.add_node("technical_agent", technical_agent)
    builder.add_node("general_agent", general_agent)
    builder.add_node("human_approval", human_approval)
    builder.add_node("respond", respond)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify",
        route_by_category,
        {
            "billing": "billing_agent",
            "technical": "technical_agent",
            "general": "general_agent",
        },
    )
    builder.add_edge("billing_agent", "human_approval")
    builder.add_edge("technical_agent", "human_approval")
    builder.add_edge("general_agent", "human_approval")
    builder.add_conditional_edges("human_approval", route_on_approval, {"respond": "respond"})
    builder.add_edge("respond", END)

    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    def run_ticket(thread_id: str, ticket: str, resume_value: bool) -> None:
        config = {"configurable": {"thread_id": thread_id}}
        print(f"--- ticket [{thread_id}]: {ticket!r} ---")
        result = graph.invoke({"ticket": ticket}, config)

        if "__interrupt__" not in result:
            print("  (no interrupt raised - unexpected)")
            return

        payload = result["__interrupt__"][0].value
        print(f"  category: routed to a specialist, draft awaiting approval")
        print(f"  draft: {payload['draft']}")

        final = graph.invoke(Command(resume=resume_value), config)
        print(f"  {final['final_response']}\n")

    run_ticket(
        "ticket-1", "I was charged twice for my subscription this month.", resume_value=True
    )
    run_ticket(
        "ticket-2", "The app crashes every time I try to export a PDF.", resume_value=False
    )


if __name__ == "__main__":
    main()
