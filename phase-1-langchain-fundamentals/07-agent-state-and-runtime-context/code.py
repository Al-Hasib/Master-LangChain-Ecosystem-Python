"""
Phase 1 - Topic 07: Agent State & Runtime Context

Run:
    python code.py
"""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

FAKE_ACCOUNTS = {
    "user_123": {"name": "Sarah Chen", "balance": 1204.50},
    "user_456": {"name": "Amit Rao", "balance": 87.10},
}


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
        from langchain.tools import ToolRuntime, tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    @dataclass
    class Context:
        user_id: str

    @tool
    def get_account_balance(runtime: ToolRuntime[Context]) -> str:
        """Get the current user's account balance. Takes no arguments from the model -
        the user is identified by runtime context, never by anything the model provides.
        """
        account = FAKE_ACCOUNTS.get(runtime.context.user_id)
        if not account:
            return "Unknown user"
        return f"{account['name']}'s balance is ${account['balance']:.2f}"

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[get_account_balance],
        context_schema=Context,
    )

    question = "What's my account balance?"
    for user_id in ["user_123", "user_456"]:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            context=Context(user_id=user_id),
        )
        print(f"[context.user_id={user_id}] {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
