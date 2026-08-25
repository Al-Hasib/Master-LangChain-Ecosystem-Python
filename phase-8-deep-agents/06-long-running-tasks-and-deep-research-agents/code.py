"""
Phase 8 - Topic 06: Long-Running Tasks & Deep Research Agents

Run:
    python code.py

This is the phase project, scoped down to: planning (write_todos) + a research
subagent (DuckDuckGo search) + filesystem notes, synthesized into a final report.
See doc.md for the scoping decisions vs. the full README diagram.
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
        from langchain.agents.middleware import TodoListMiddleware
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    try:
        from deepagents import create_deep_agent
    except ImportError:
        sys.exit("Missing dependency. Run: pip install deepagents")

    model = init_chat_model("gpt-4o-mini", model_provider="openai")

    # --- Web search tool: same DuckDuckGo pattern as Phase 1 Topic 11 ---
    @tool
    def web_search(query: str) -> str:
        """Search the web for current information not in your training data."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "Web search unavailable: duckduckgo-search not installed."
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
        except Exception as exc:  # noqa: BLE001
            return f"Search failed (network issue?): {exc}"
        if not results:
            return "No results found."
        return "\n".join(f"- {r['title']}: {r['body'][:150]}" for r in results)

    agent = create_deep_agent(
        model=model,
        tools=[web_search],
        system_prompt=(
            "You are a research lead. Plan with write_todos first. For EACH topic "
            "to research, delegate to the researcher subagent (it will search and "
            "save notes to a file). Once all notes are written, read them back "
            "with read_file and write a short final comparison report."
        ),
        middleware=[TodoListMiddleware()],
        subagents=[
            {
                "name": "researcher",
                "description": (
                    "Researches ONE named topic using web_search and saves its "
                    "findings to notes/<topic>.md via write_file. Use once per topic."
                ),
                "system_prompt": (
                    "You research exactly one topic: search the web for it, then "
                    "write_file a short markdown summary of what you found to "
                    "notes/<topic-slug>.md. Report back only the file path you wrote."
                ),
                "tools": [web_search],
            },
        ],
    )

    question = (
        "Research 'LangChain' and 'LangGraph' (one topic each), save notes for "
        "each, then read the notes back and write a 3-sentence comparison."
    )
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    print("--- Final plan (result['todos']) ---")
    for todo in result.get("todos", []):
        print(f"  [{todo.get('status')}] {todo.get('content')}")

    print("\n--- Files written during research (result['files']) ---")
    for path in result.get("files", {}):
        print(f"  {path}")

    print(f"\n--- Final report ---\n{result['messages'][-1].content}")


if __name__ == "__main__":
    main()
