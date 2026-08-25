"""
Phase 2 - Topic 03: Local & Alternative Providers (Ollama, OpenRouter)

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

PROMPT = "In one sentence, what is retrieval-augmented generation?"


def try_ollama() -> None:
    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model_name = os.getenv("OLLAMA_MODEL", "llama3.1")
    try:
        model = init_chat_model(model_name, model_provider="ollama", temperature=0)
        response = model.invoke(PROMPT)
        print(f"[ollama:{model_name}] {response.content}")
    except ImportError:
        print("[skipped] ollama: run `pip install langchain-ollama` to include it")
    except Exception as exc:  # noqa: BLE001 - connection errors vary by platform
        print(
            f"[skipped] ollama: couldn't reach a local Ollama server ({exc}).\n"
            f"          Install Ollama, run `ollama pull {model_name}`, and make "
            "sure the app is running."
        )


def try_openrouter() -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[skipped] openrouter: OPENROUTER_API_KEY not set in .env")
        return
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # OpenRouter is OpenAI-COMPATIBLE, not a langchain provider string - reached via
    # a base_url override on ChatOpenAI, still the same downstream .invoke() call.
    model = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model="meta-llama/llama-3.1-8b-instruct",
        temperature=0,
    )
    response = model.invoke(PROMPT)
    print(f"[openrouter:meta-llama/llama-3.1-8b-instruct] {response.content}")


def main() -> None:
    print("--- Local model via Ollama ---")
    try_ollama()

    print("\n--- Many providers via OpenRouter ---")
    try_openrouter()


if __name__ == "__main__":
    main()
