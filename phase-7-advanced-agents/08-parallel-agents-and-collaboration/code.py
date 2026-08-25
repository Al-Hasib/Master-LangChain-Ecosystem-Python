"""
Phase 7 - Topic 08: Parallel Agents & Collaboration

Run:
    python code.py

Demonstrates: fanning the SAME question out to multiple agents concurrently
(concurrent.futures.ThreadPoolExecutor - real concurrency, stdlib, no extra deps),
timing it against sequential execution, then merging the answers into one result.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

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
        from langchain.agents import create_agent
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # Three agents sharing a task but each given a different "lens" via system_prompt -
    # a lightweight way to get genuinely different perspectives without different tools.
    LENSES = {
        "optimist": "Answer as an optimist: focus on the upside and opportunities.",
        "skeptic": "Answer as a skeptic: focus on risks, caveats, and what could go wrong.",
        "conciser": "Answer in one tight sentence, no elaboration.",
    }
    agents = {
        name: create_agent(model="gpt-4o-mini", tools=[], system_prompt=prompt)
        for name, prompt in LENSES.items()
    }

    question = "Should a small team adopt a multi-agent LLM architecture for their product?"

    def ask(agent_name: str) -> tuple[str, str]:
        agent = agents[agent_name]
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        return agent_name, result["messages"][-1].content

    print(f"Question: {question}\n")

    # --- Fan-out: submit all three BEFORE collecting any result, so they overlap ---
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(agents)) as executor:
        futures = [executor.submit(ask, name) for name in agents]
        answers = dict(future.result() for future in futures)
    elapsed = time.perf_counter() - start

    print(f"--- Fan-out results (ran concurrently, {elapsed:.1f}s wall-clock) ---")
    for name, answer in answers.items():
        print(f"  [{name}] {answer}")

    # --- Fan-in: merge the three perspectives with one more model call ---
    merger = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    combined_input = "\n".join(f"{name}: {answer}" for name, answer in answers.items())
    merge_result = merger.invoke(
        f"Question: {question}\n\nThree perspectives:\n{combined_input}\n\n"
        "Write one balanced paragraph that weighs all three."
    )
    print(f"\n--- Merged answer ---\n  {merge_result.content}")


if __name__ == "__main__":
    main()
