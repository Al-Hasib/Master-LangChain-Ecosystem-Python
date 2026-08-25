"""
Phase 6 - Topic 09: LangGraph Runtime & Production Architecture

Run:
    python code.py

Not new graph mechanics - a small readiness-checklist script. It compiles
Topic 03's classify-then-route graph and reports pass/fail against the
production concerns this topic's doc.md covers (durable checkpointer, etc.).
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
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    class State(TypedDict):
        message: str
        category: str
        response: str

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    VALID_CATEGORIES = ("billing", "technical", "general")

    def classify(state: State) -> dict:
        raw = model.invoke(
            "Classify into one word - billing, technical, or general: "
            f"{state['message']!r}"
        ).content.strip().lower()
        return {"category": raw if raw in VALID_CATEGORIES else "general"}

    def respond(state: State) -> dict:
        return {"response": f"[{state['category']}] handled."}

    builder = StateGraph(State)
    builder.add_node("classify", classify)
    builder.add_node("respond", respond)
    builder.add_edge(START, "classify")
    builder.add_edge("classify", "respond")
    builder.add_edge("respond", END)

    # Deliberately using InMemorySaver here, same as every earlier topic - the
    # checklist below is what tells you this is NOT production-ready as-is.
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)  # noqa: F841 (compiled to prove it works)

    print("=== Production readiness checklist for this graph ===\n")

    checks = []

    # 1) Durable checkpointer? (checked against the object WE compiled with,
    # not by introspecting the compiled graph - keeps this independent of any
    # particular internal attribute name.)
    checkpointer_type = type(checkpointer).__name__
    is_durable = checkpointer_type not in ("InMemorySaver", "MemorySaver", "NoneType")
    checks.append(
        (
            "Durable checkpointer (survives a process restart)",
            is_durable,
            f"compiled with {checkpointer_type} - swap for a Postgres/SQLite-backed "
            "saver before deploying" if not is_durable else checkpointer_type,
        )
    )

    # 2) Server / long-lived process, vs. one-off script run.
    checks.append(
        (
            "Served by a long-lived process (not `python code.py` per request)",
            False,
            "this file is a one-off script - production needs a server "
            "(FastAPI endpoint calling .invoke()/.stream(), or a managed runtime)",
        )
    )

    # 3) Resumable across restarts (depends directly on check #1).
    checks.append(
        (
            "Paused/interrupted threads survive a redeploy",
            is_durable,
            "only true once the checkpointer above is durable",
        )
    )

    # 4) Observability wired up.
    has_tracing = bool(os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_TRACING_V2"))
    checks.append(
        (
            "Tracing/observability configured (Phase 9, LangSmith)",
            has_tracing,
            "LANGSMITH_API_KEY / LANGCHAIN_TRACING_V2 not set - fine for this course, "
            "required before shipping" if not has_tracing else "tracing env vars present",
        )
    )

    for name, passed, note in checks:
        mark = "PASS" if passed else "TODO"
        print(f"  [{mark}] {name}")
        print(f"         {note}")

    print("\nThis graph is correct - readiness here is entirely about DEPLOYMENT")
    print("configuration, not about rewriting any node or edge above.")


if __name__ == "__main__":
    main()
