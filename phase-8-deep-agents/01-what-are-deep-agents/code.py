"""
Phase 8 - Topic 01: What are Deep Agents?

Run:
    python code.py

Demonstrates the baseline problem (Phase 1's create_agent loop has no persistent
scratch space or plan) and introduces the simplest possible create_deep_agent() call.
Confirmed against https://docs.langchain.com/oss/python/deepagents/quickstart and
https://docs.langchain.com/oss/python/deepagents/overview.
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
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    try:
        from deepagents import create_deep_agent
    except ImportError:
        sys.exit("Missing dependency. Run: pip install deepagents")

    model = init_chat_model("gpt-4o-mini", model_provider="openai")

    @tool
    def word_count(text: str) -> int:
        """Count words in a piece of text."""
        return len(text.split())

    question = (
        "Draft a 3-sentence pitch for a note-taking app, then tell me the word "
        "count of your pitch."
    )

    # --- Baseline: Phase 1's create_agent (the loop from Topic 06) ---
    print("=== create_agent (Phase 1 baseline) ===")
    plain_agent = create_agent(
        model=model,
        tools=[word_count],
        system_prompt="You are a helpful assistant. Use tools when relevant.",
    )
    plain_result = plain_agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(f"Messages in trace: {len(plain_result['messages'])}")
    print(f"Final answer: {plain_result['messages'][-1].content}\n")
    # Nothing here tracks "am I done planning?" or gives the model scratch space -
    # everything the model produces lives only in this one message list.

    # --- Deep agent: same tools, zero extra config ---
    print("=== create_deep_agent (same task, deepagents harness) ===")
    deep_agent = create_deep_agent(
        model=model,
        tools=[word_count],
        system_prompt="You are a helpful assistant. Use tools when relevant.",
    )
    deep_result = deep_agent.invoke({"messages": [{"role": "user", "content": question}]})
    tool_names_used = sorted(
        {
            call["name"]
            for message in deep_result["messages"]
            for call in (getattr(message, "tool_calls", []) or [])
        }
    )
    print(f"Messages in trace: {len(deep_result['messages'])}")
    print(f"Tool(s) actually called: {tool_names_used or 'none'}")
    # Even though the model didn't need them for this simple question, the deep
    # agent's graph state already carries a "files" key - that's the virtual
    # filesystem (Topic 04) sitting there ready for scratch-space use, and a
    # "task" tool (Topic 05) is bound and available for delegation, at no
    # extra configuration cost.
    print(
        f"Graph state also carries a 'files' key: "
        f"{'files' in deep_result} -> {deep_result.get('files', {})}"
    )
    print(f"Final answer: {deep_result['messages'][-1].content}")


if __name__ == "__main__":
    main()
