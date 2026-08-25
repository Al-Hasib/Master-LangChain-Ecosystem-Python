"""
Phase 0 - Topic 02: Tokens, Context Windows & Model Parameters

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


SAMPLE_TEXT = (
    "LangChain is a framework for building applications powered by language models. "
    "It provides abstractions for models, prompts, tools, and agents."
)


def show_token_count(text: str) -> None:
    try:
        import tiktoken
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    encoding = tiktoken.encoding_for_model("gpt-4o-mini")
    tokens = encoding.encode(text)
    words = text.split()

    print(f"Text: {text!r}")
    print(f"Word count:  {len(words)}")
    print(f"Token count: {len(tokens)}")
    print(f"First 10 token ids: {tokens[:10]}")
    print(f"Decoded back:        {encoding.decode(tokens[:10])!r}")


def compare_temperatures(client, model: str) -> None:
    prompt = "Give a one-sentence tagline for an AI coding assistant."

    print("\n--- temperature=0 (should repeat) ---")
    for i in range(2):
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=30,
        )
        print(f"  run {i + 1}: {response.choices[0].message.content}")

    print("\n--- temperature=1 (likely to vary) ---")
    for i in range(2):
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=30,
        )
        print(f"  run {i + 1}: {response.choices[0].message.content}")


def main() -> None:
    print("=== Token counting (no API key required) ===")
    show_token_count(SAMPLE_TEXT)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(
            "\nSkipping temperature comparison: OPENAI_API_KEY not set. "
            "Set it in .env to run that part."
        )
        return

    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    client = OpenAI(api_key=api_key)
    print("\n=== Temperature comparison ===")
    compare_temperatures(client, model="gpt-4o-mini")


if __name__ == "__main__":
    main()
