"""
Phase 7 - Topic 03: Context Management & Middleware

Run:
    python code.py

Demonstrates: a hand-rolled @before_model middleware that trims message history to
the last N messages (using RemoveMessage so the shrink actually sticks, since
state["messages"] uses an additive reducer) - plus a confirmed-working use of the
built-in SummarizationMiddleware as the production-grade alternative.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

KEEP_LAST_N = 6


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
        from langchain.agents.middleware import SummarizationMiddleware, before_model
        from langchain_core.messages import RemoveMessage
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # --- 1) Hand-rolled trim-to-last-N middleware ---
    @before_model
    def trim_to_last_n(state, runtime):
        messages = state["messages"]
        if len(messages) <= KEEP_LAST_N:
            return None  # nothing to trim, continue normally
        to_drop = messages[:-KEEP_LAST_N]
        # RemoveMessage(id=...) is the only way to actually shrink state["messages"] -
        # the add_messages reducer deletes entries whose id matches a RemoveMessage.
        return {"messages": [RemoveMessage(id=m.id) for m in to_drop]}

    agent = create_agent(model="gpt-4o-mini", tools=[], middleware=[trim_to_last_n])

    # Seed a long fake history (12 prior turns) plus a final question, simulating a
    # conversation that has been running for a while before this invoke() call.
    seeded_history = []
    for i in range(6):
        seeded_history.append({"role": "user", "content": f"Fact #{i}: my lucky number is {i}."})
        seeded_history.append({"role": "assistant", "content": f"Noted, lucky number {i}."})
    seeded_history.append({"role": "user", "content": "What did I just tell you, in one word?"})

    print(f"Messages sent into invoke(): {len(seeded_history)}")
    result = agent.invoke({"messages": seeded_history})
    print(f"Messages in state AFTER the trimming middleware ran: {len(result['messages'])}")
    print(f"(kept at most {KEEP_LAST_N} - old facts were dropped before reaching the model)")
    print(f"Final answer: {result['messages'][-1].content}\n")

    # --- 2) Confirm the built-in SummarizationMiddleware also works as documented ---
    print("--- Built-in SummarizationMiddleware (production alternative) ---")
    summarizing_agent = create_agent(
        model="gpt-4o-mini",
        tools=[],
        middleware=[
            SummarizationMiddleware(
                model="gpt-4o-mini",
                trigger=("messages", 20),  # summarize once history passes 20 messages
                keep=("messages", 6),  # always keep the last 6 verbatim
            )
        ],
    )
    result_2 = summarizing_agent.invoke(
        {"messages": [{"role": "user", "content": "Say 'summarization middleware wired up ok' and nothing else."}]}
    )
    print(f"Final answer: {result_2['messages'][-1].content}")


if __name__ == "__main__":
    main()
