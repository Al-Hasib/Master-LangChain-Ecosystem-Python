"""
Phase 1 - Topic 02: Models & init_chat_model

Run:
    python code.py
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

PROMPT = "In one sentence, what makes a chat model different from a completion model?"


def timed_invoke(model, label: str) -> None:
    start = time.perf_counter()
    response = model.invoke(PROMPT)
    elapsed = time.perf_counter() - start
    print(f"[{label}] ({elapsed:.2f}s) {response.content}")


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )
    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # Same constructor, same return type, same .invoke() call site - only the
    # provider string changes.
    openai_model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    timed_invoke(openai_model, "openai:gpt-4o-mini")

    if os.getenv("ANTHROPIC_API_KEY"):
        anthropic_model = init_chat_model(
            "claude-3-5-haiku-latest", model_provider="anthropic", temperature=0
        )
        timed_invoke(anthropic_model, "anthropic:claude-3-5-haiku")
    else:
        print(
            "[skipped] Set ANTHROPIC_API_KEY in .env to also run this prompt "
            "against Anthropic with the exact same code path."
        )


if __name__ == "__main__":
    main()
