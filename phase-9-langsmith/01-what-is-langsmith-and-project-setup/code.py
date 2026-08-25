"""
Phase 9 - Topic 01: What is LangSmith? & Project Setup

Confirms your LangSmith setup works: reads the tracing env vars, makes one
traced LLM call, and prints where to go look for it in the LangSmith web app.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def require_langsmith_key() -> None:
    # LANGCHAIN_API_KEY / LANGCHAIN_PROJECT are the names already in .env.example.
    # LangSmith's current docs also accept LANGSMITH_API_KEY / LANGSMITH_PROJECT -
    # the SDK reads either prefix, so either works; this repo standardizes on the
    # LANGCHAIN_* spelling to match .env.example.
    if not os.getenv("LANGCHAIN_API_KEY"):
        sys.exit(
            "Missing LANGCHAIN_API_KEY.\n"
            "This topic needs a real LangSmith account/API key to demonstrate actual "
            "tracing (get one free at https://smith.langchain.com/).\n"
            "1) cp ../../.env.example ../../.env\n"
            "2) fill in LANGCHAIN_API_KEY\n"
            "3) also set LANGCHAIN_TRACING_V2=true in ../../.env\n"
            "4) re-run"
        )
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
        sys.exit(
            "LANGCHAIN_API_KEY is set, but LANGCHAIN_TRACING_V2 is not \"true\".\n"
            "Set LANGCHAIN_TRACING_V2=true in ../../.env and re-run - without it, "
            "the SDK has a key but tracing stays switched off."
        )


def main() -> None:
    require_openai_key()
    require_langsmith_key()
    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # Default project name if the viewer didn't set one - matches .env.example's
    # placeholder so traces land somewhere predictable.
    project = os.getenv("LANGCHAIN_PROJECT", "langchain-ecosystem-course")

    print(f"Tracing enabled: LANGCHAIN_TRACING_V2={os.getenv('LANGCHAIN_TRACING_V2')}")
    print(f"Target project:  {project}")
    print()

    # No special "start a trace" call needed - once the env vars above are set,
    # every LangChain construct (init_chat_model included) traces itself.
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    response = model.invoke("In one sentence, what does an observability tool do?")

    print(f"Model response: {response.content}\n")
    print("This call was traced. Since viewing the trace tree itself requires a real")
    print("LangSmith account, go look for it here:")
    print(f"  https://smith.langchain.com/  ->  project \"{project}\"  ->  latest run")


if __name__ == "__main__":
    main()
