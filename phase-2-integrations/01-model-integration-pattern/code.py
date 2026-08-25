"""
Phase 2 - Topic 01: Model Integration Pattern

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def summarize(model, text: str) -> str:
    """Doesn't know or care which provider `model` came from - it only relies on
    the standard BaseChatModel interface (.invoke -> object with .content)."""
    response = model.invoke(f"Summarize in one short sentence: {text}")
    return response.content


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

    text = (
        "LangChain provides standard interfaces for chat models, tools, and agents "
        "so application code doesn't need to be rewritten per model provider."
    )

    # The ONLY place a provider name appears - everything past this line is
    # provider-agnostic. In a real app this would read MODEL_PROVIDER from config.
    providers = [
        ("openai", "gpt-4o-mini", "OPENAI_API_KEY"),
        ("anthropic", "claude-3-5-haiku-latest", "ANTHROPIC_API_KEY"),
    ]

    for provider, model_name, key_env in providers:
        if not os.getenv(key_env):
            print(f"[skipped] {provider}: {key_env} not set in .env")
            continue
        model = init_chat_model(model_name, model_provider=provider, temperature=0)
        result = summarize(model, text)  # identical call, any provider
        print(f"[{provider}] {result}")


if __name__ == "__main__":
    main()
