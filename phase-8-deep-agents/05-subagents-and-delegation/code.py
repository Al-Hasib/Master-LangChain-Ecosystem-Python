"""
Phase 8 - Topic 05: Subagents & Delegation

Run:
    python code.py

Confirmed API: create_deep_agent(subagents=[{"name", "description", "system_prompt",
"tools"}]) - subagents run in an isolated context and return one final report via the
built-in `task` tool. See https://docs.langchain.com/oss/python/deepagents/subagents
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
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    try:
        from deepagents import create_deep_agent
    except ImportError:
        sys.exit("Missing dependency. Run: pip install deepagents")

    model = init_chat_model("gpt-4o-mini", model_provider="openai")

    @tool
    def lookup_fact(claim: str) -> str:
        """Check a claim against a small offline reference of known facts."""
        known_true = [
            "chroma is open source",
            "faiss was built by meta",
            "duckduckgo search requires no api key",
        ]
        claim_lower = claim.lower()
        matched = any(fact in claim_lower or claim_lower in fact for fact in known_true)
        return "TRUE - matches known reference" if matched else "UNVERIFIED - no matching reference"

    agent = create_deep_agent(
        model=model,
        system_prompt=(
            "You answer user questions. When a claim needs verification, delegate "
            "to the fact-checker subagent via the task tool instead of guessing."
        ),
        subagents=[
            {
                "name": "fact-checker",
                "description": (
                    "Verifies ONE specific factual claim using lookup_fact and "
                    "reports back TRUE/UNVERIFIED with a one-line reason."
                ),
                "system_prompt": (
                    "You check exactly one claim using lookup_fact and report "
                    "TRUE/UNVERIFIED plus a one-line reason. Nothing else."
                ),
                "tools": [lookup_fact],
            },
        ],
    )

    question = "Is it true that FAISS was built by Meta? Verify before answering."
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    task_calls = [
        call
        for message in result["messages"]
        for call in (getattr(message, "tool_calls", []) or [])
        if call["name"] == "task"
    ]
    print(f"Delegated to a subagent {len(task_calls)} time(s): {task_calls}")
    print(f"Messages in the MAIN conversation: {len(result['messages'])}")
    # Notice how few messages this is - the fact-checker's own tool-call back-and-
    # forth happened in an isolated context and never joined this list, only its
    # final report did.
    print(f"\nFinal answer: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
