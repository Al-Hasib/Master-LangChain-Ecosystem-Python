"""
Phase 9 - Topic 04: Prompt Management

Demonstrates local-version-control prompts (needs nothing but Python) and, when
a LangSmith key is present, a real round trip through the Prompt Hub via
Client.push_prompt / Client.pull_prompt.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# --- Pattern 1: local version control ---------------------------------------
# A dedicated module-level dict, versioned with a comment per entry, reviewed in
# normal PRs like any other code. No network call, no LangSmith account needed.
PROMPTS = {
    "qa-prompt": {
        "version": "v2 (2026-08) - tightened to force concise answers",
        "template": "Answer the question in one concise sentence: {question}",
    },
    # "v1 (2026-06) - original, unbounded length - superseded by v2 above"
}


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def main() -> None:
    require_openai_key()
    try:
        from langchain.chat_models import init_chat_model
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    print("=== Pattern 1: local version control ===")
    entry = PROMPTS["qa-prompt"]
    print(f"Using prompts.py-style entry: {entry['version']}")
    local_prompt = ChatPromptTemplate.from_template(entry["template"])
    local_chain = local_prompt | model
    result = local_chain.invoke({"question": "What is a vector database?"})
    print(f"Result: {result.content}\n")

    print("=== Pattern 2: LangSmith Prompt Hub ===")
    # This part needs a real LangSmith account - push_prompt/pull_prompt are real
    # network calls to your workspace, not something that can be faked locally.
    if not os.getenv("LANGCHAIN_API_KEY"):
        print(
            "[skipped] LANGCHAIN_API_KEY not set - Prompt Hub is a hosted feature and "
            "needs a real account (free at https://smith.langchain.com/).\n"
            "1) cp ../../.env.example ../../.env\n2) fill in LANGCHAIN_API_KEY\n"
            "3) re-run to see the real push_prompt/pull_prompt round trip."
        )
        return

    try:
        from langsmith import Client
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    client = Client()
    prompt_name = "langchain-course-phase9-qa-prompt"
    hub_prompt = ChatPromptTemplate.from_template(
        "Answer the question in one concise sentence: {question}"
    )

    # Pushes a new commit under this name (creates the prompt on first push).
    push_url = client.push_prompt(prompt_name, object=hub_prompt)
    print(f"Pushed prompt \"{prompt_name}\" -> {push_url}")

    # Pulls the latest commit back - what your app would call at runtime instead
    # of reading a local template string.
    pulled_prompt = client.pull_prompt(prompt_name)
    pulled_chain = pulled_prompt | model
    result = pulled_chain.invoke({"question": "What is a retriever?"})
    print(f"Result from PULLED prompt: {result.content}")

    print(
        "\nOpen the prompt in the LangSmith UI to see its commit history "
        f"(each push_prompt call adds one): {push_url}"
    )


if __name__ == "__main__":
    main()
