"""
Phase 6 - Topic 07: Time Travel & Error Handling

Run:
    python code.py

Demonstrates (1) listing checkpoint history and replaying from a past state
("time travel"), and (2) automatic node-level retries via RetryPolicy.
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
        from langgraph.types import RetryPolicy
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # === Part 1: time travel over Topic 02's 3-node pipeline =================
    class State(TypedDict):
        topic: str
        greeting: str
        reply: str
        final: str

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    def greet(state: State) -> dict:
        return {"greeting": f"Let's talk about {state['topic']}."}

    def call_model(state: State) -> dict:
        prompt = f"{state['greeting']} In one sentence, why does it matter?"
        return {"reply": model.invoke(prompt).content}

    def format_output(state: State) -> dict:
        return {"final": f"{state['greeting']}\n{state['reply']}"}

    builder = StateGraph(State)
    builder.add_node("greet", greet)
    builder.add_node("call_model", call_model)
    builder.add_node("format_output", format_output)
    builder.add_edge(START, "greet")
    builder.add_edge("greet", "call_model")
    builder.add_edge("call_model", "format_output")
    builder.add_edge("format_output", END)

    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "time-travel-demo"}}
    print("--- run 1: normal, full run ---")
    result = graph.invoke({"topic": "LangGraph"}, config)
    print(f"  final: {result['final']}\n")

    print("--- checkpoint history (newest first) ---")
    history = list(graph.get_state_history(config))
    for snapshot in history:
        print(f"  next={snapshot.next!r}  values.keys()={list(snapshot.values.keys())}")

    # Find the checkpoint saved right after "greet" ran (its "next" step is
    # "call_model") and replay from there.
    replay_point = next(s for s in history if s.next == ("call_model",))
    print(f"\n--- replaying from right after 'greet' (checkpoint_id={replay_point.config['configurable']['checkpoint_id'][:8]}...) ---")
    replayed = graph.invoke(None, replay_point.config)
    print(f"  final: {replayed['final']}")
    print("  (call_model + format_output re-ran; greet's saved result was reused)\n")

    # === Part 2: automatic retry on node failure via RetryPolicy ==============
    print("--- retry demo: a node that fails its first two attempts ---")

    class RetryState(TypedDict):
        attempts: int
        result: str

    call_count = {"n": 0}

    def flaky_step(state: RetryState) -> dict:
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise RuntimeError(f"simulated transient failure #{call_count['n']}")
        return {"result": f"succeeded on attempt {call_count['n']}"}

    retry_builder = StateGraph(RetryState)
    retry_builder.add_node(
        "flaky_step",
        flaky_step,
        # Retries the WHOLE node automatically on matching exceptions - no
        # manual try/except loop needed inside the node itself.
        retry_policy=RetryPolicy(max_attempts=3, retry_on=(RuntimeError,)),
    )
    retry_builder.add_edge(START, "flaky_step")
    retry_builder.add_edge("flaky_step", END)
    retry_graph = retry_builder.compile()

    retry_result = retry_graph.invoke({"attempts": 0})
    print(f"  {retry_result['result']}")


if __name__ == "__main__":
    main()
