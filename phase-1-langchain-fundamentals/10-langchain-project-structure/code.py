"""
Phase 1 - Topic 10: LangChain Project Structure

Demonstrates the config / tools / agent-wiring split IN ONE FILE (since this is a
single-topic teaching example). In a real project, each commented section below
becomes its own module - see doc.md for the target multi-file layout.

Run:
    python code.py
"""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# config.py  (in a real project: its own file, imported everywhere else)
# ============================================================================
@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    model_name: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            sys.exit(
                "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
                "2) fill in your key\n3) re-run"
            )
        return cls(openai_api_key=api_key)


# ============================================================================
# tools/math_tools.py  (in a real project: its own file. The plain function
# below is unit-testable directly, with no langchain import at all - only the
# decorated version needs it.)
# ============================================================================
def add_numbers(a: float, b: float) -> float:
    return a + b


def make_add_tool():
    from langchain.tools import tool

    @tool
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return add_numbers(a, b)

    return add


# ============================================================================
# agents/research_agent.py  (in a real project: its own file, imports from
# config.py and tools/)
# ============================================================================
def build_agent(settings: Settings):
    from langchain.agents import create_agent

    return create_agent(
        model=settings.model_name,
        tools=[make_add_tool()],
        system_prompt="You are a helpful assistant.",
    )


# ============================================================================
# main.py  (in a real project: the thin entry point)
# ============================================================================
def main() -> None:
    settings = Settings.from_env()
    agent = build_agent(settings)

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's 41 plus 1?"}]}
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    try:
        import langchain  # noqa: F401
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    main()
