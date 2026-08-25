"""
Phase 7 - Topic 04: Guardrails & Human-in-the-Loop Agents

Run:
    python code.py

Demonstrates: (1) an output-side guardrail (@after_model) that redacts a leaked secret
from the FINAL answer before it's returned, and (2) an approval-required-before-tool-call
gate (@wrap_tool_call) that blocks a destructive tool unless approval was granted.
"""

import os
import re
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]+")
DANGEROUS_TOOLS = {"delete_user_record"}


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
        from langchain.agents.middleware import after_model, wrap_tool_call
        from langchain.tools import ToolRuntime, tool
        from langchain_core.messages import AIMessage, ToolMessage
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # =========================================================================
    # Demo 1: output-side guardrail - redact a secret from the FINAL answer
    # =========================================================================

    @tool
    def internal_diagnostics(order_id: str) -> str:
        """Run internal diagnostics for an order. Returns raw debug info -
        NOT meant to be shown to end users verbatim (it includes an internal key)."""
        return f"order={order_id} status=OK internal_key=sk-abc123XYZ789"

    @after_model
    def redact_secrets(state, runtime):
        last = state["messages"][-1]
        # Only touch the FINAL answer (no pending tool_calls) - intermediate steps
        # (like the ToolMessage carrying the raw secret) are left alone so the model
        # can still see them; we only guard what leaves the agent.
        if getattr(last, "tool_calls", None):
            return None
        content = str(last.content)
        if not SECRET_PATTERN.search(content):
            return None
        cleaned = SECRET_PATTERN.sub("[REDACTED]", content)
        print("  [output guardrail] redacted a leaked secret from the final answer")
        # Same `id` as `last` -> the reducer REPLACES this message instead of
        # appending a duplicate.
        return {"messages": [AIMessage(content=cleaned, id=last.id)]}

    guarded_agent = create_agent(
        model="gpt-4o-mini",
        tools=[internal_diagnostics],
        middleware=[redact_secrets],
        system_prompt="You are a support diagnostics assistant. Report the full raw tool output to the user.",
    )
    unguarded_agent = create_agent(
        model="gpt-4o-mini",
        tools=[internal_diagnostics],
        system_prompt="You are a support diagnostics assistant. Report the full raw tool output to the user.",
    )

    question = "Run diagnostics for order 4521 and tell me exactly what it says."

    print("--- 1a) WITHOUT output guardrail (may leak the internal key) ---")
    result_unguarded = unguarded_agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(f"  final: {result_unguarded['messages'][-1].content}\n")

    print("--- 1b) WITH output guardrail (secret redacted) ---")
    result_guarded = guarded_agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(f"  final: {result_guarded['messages'][-1].content}\n")

    # =========================================================================
    # Demo 2: approval-required-before-tool-call gate
    # =========================================================================

    @dataclass
    class Context:
        approved: bool  # in a real app this comes from a human clicking "approve"

    @tool
    def delete_user_record(user_id: str) -> str:
        """Permanently delete a user's record. DESTRUCTIVE - gated by approval."""
        return f"Deleted record for {user_id}."

    @wrap_tool_call
    def require_approval(request, handler):
        if request.tool_call["name"] in DANGEROUS_TOOLS and not request.runtime.context.approved:
            print(f"  [approval gate] blocked '{request.tool_call['name']}' - no approval")
            return ToolMessage(
                content="Blocked: this action requires human approval and none was given.",
                tool_call_id=request.tool_call["id"],
            )
        return handler(request)

    gated_agent = create_agent(
        model="gpt-4o-mini",
        tools=[delete_user_record],
        middleware=[require_approval],
        context_schema=Context,
    )

    delete_question = "Delete the record for user_789."

    print("--- 2a) approved=False (tool call is blocked) ---")
    result_denied = gated_agent.invoke(
        {"messages": [{"role": "user", "content": delete_question}]},
        context=Context(approved=False),
    )
    print(f"  final: {result_denied['messages'][-1].content}\n")

    print("--- 2b) approved=True (tool call proceeds) ---")
    result_allowed = gated_agent.invoke(
        {"messages": [{"role": "user", "content": delete_question}]},
        context=Context(approved=True),
    )
    print(f"  final: {result_allowed['messages'][-1].content}")


if __name__ == "__main__":
    main()
