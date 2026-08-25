"""
Phase 8 - Topic 04: Filesystem Tools & Context Management

Run:
    python code.py

Confirmed API: filesystem tools (ls, read_file, write_file, edit_file, glob, grep,
delete) are bound by default on create_deep_agent, backed by graph state (virtual, not
real disk). See https://docs.langchain.com/oss/python/deepagents/middleware
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
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    try:
        from deepagents import create_deep_agent
    except ImportError:
        sys.exit("Missing dependency. Run: pip install deepagents")

    model = init_chat_model("gpt-4o-mini", model_provider="openai")

    # A deliberately "verbose" tool - simulates a raw web search result the model
    # should offload to a file rather than keep re-reading in full every turn.
    @tool
    def fetch_raw_source(topic: str) -> str:
        """Fetch a long raw source document about a topic (simulated)."""
        return (
            f"[RAW SOURCE about {topic}] "
            + ("Lorem ipsum background detail. " * 40)
            + f"KEY FACT: {topic} was chosen for this course because it's free and "
            "requires no API key."
        )

    agent = create_deep_agent(
        model=model,
        tools=[fetch_raw_source],
        system_prompt=(
            "When fetch_raw_source returns a long result, immediately write_file "
            "it to 'notes/<topic>.md' instead of repeating it in your reply. Read "
            "the file back with read_file only when you actually need its content."
        ),
    )

    # Single run, two phases: fetch + save, THEN a follow-up that needs the saved
    # content read back - proves the file persists across turns in one invoke().
    question = (
        "Fetch the raw source for 'duckduckgo-search', save it to a file, then "
        "later in this same task read the file back and tell me the KEY FACT it "
        "contains."
    )
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    print("--- Filesystem tool calls seen during the run ---")
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", []) or []:
            if call["name"] in {"write_file", "read_file", "ls", "edit_file"}:
                print(f"  {call['name']}({call['args']})")

    print("\n--- Final virtual filesystem state (result['files']) ---")
    for path, contents in result.get("files", {}).items():
        preview = contents.get("content", contents) if isinstance(contents, dict) else contents
        preview = str(preview)[:80]
        print(f"  {path}: {preview}...")

    print(f"\nFinal answer: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
