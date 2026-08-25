"""
Phase 2 - Topic 02: Provider Walkthrough - OpenAI, Anthropic, Gemini

Run:
    python code.py
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

PROMPT = "In one sentence, what's a good use case for retrieval-augmented generation?"

# (provider string, model name, required env var, package to install if missing)
PROVIDERS = [
    ("openai", "gpt-4o-mini", "OPENAI_API_KEY", "langchain-openai"),
    ("anthropic", "claude-3-5-haiku-latest", "ANTHROPIC_API_KEY", "langchain-anthropic"),
    ("google_genai", "gemini-2.0-flash", "GOOGLE_API_KEY", "langchain-google-genai"),
]


def main() -> None:
    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    ran_any = False
    for provider, model_name, key_env, package in PROVIDERS:
        if not os.getenv(key_env):
            print(f"[skipped] {provider}: set {key_env} in .env to include it")
            continue
        try:
            model = init_chat_model(model_name, model_provider=provider, temperature=0)
        except ImportError:
            print(f"[skipped] {provider}: run `pip install {package}` to include it")
            continue

        start = time.perf_counter()
        response = model.invoke(PROMPT)
        elapsed = time.perf_counter() - start
        ran_any = True
        print(f"\n[{provider}:{model_name}] ({elapsed:.2f}s)")
        print(f"  {response.content}")

    if not ran_any:
        print(
            "\nNo provider keys were set. Add at least OPENAI_API_KEY to .env to see "
            "a real comparison."
        )


if __name__ == "__main__":
    main()
