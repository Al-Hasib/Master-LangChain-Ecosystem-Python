"""
Phase 0 - Topic 03: Messages & Roles (system / user / assistant)

Run:
    python code.py
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def require_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp .env.example .env\n2) fill in your key\n3) re-run"
        )
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    return OpenAI(api_key=api_key)


def ask(client, model: str, messages: list[dict]) -> str:
    response = client.chat.completions.create(model=model, messages=messages, max_tokens=80)
    return response.choices[0].message.content


def main() -> None:
    client = require_client()
    model = "gpt-4o-mini"

    # The message list IS the conversation state. Nothing is remembered between calls
    # unless we resend it ourselves.
    messages = [
        {
            "role": "system",
            "content": "You are a terse Python tutor. Answer in at most 2 sentences.",
        },
    ]

    turns = [
        "What's a list comprehension?",
        "Show one example for squaring the numbers 1 through 5.",
    ]

    for user_text in turns:
        messages.append({"role": "user", "content": user_text})

        print("--- messages sent to the model ---")
        print(json.dumps(messages, indent=2))

        reply = ask(client, model, messages)
        print(f"\n--- assistant reply ---\n{reply}\n")

        # Append the assistant's own reply before the next turn - this is what makes
        # it a conversation instead of independent single-shot calls.
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
