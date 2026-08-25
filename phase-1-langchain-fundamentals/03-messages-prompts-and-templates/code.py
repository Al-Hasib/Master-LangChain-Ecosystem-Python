"""
Phase 1 - Topic 03: Messages, Prompts & Prompt Templates

Run:
    python code.py
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
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    # --- 1) Typed message objects, built by hand (like Phase 0's dicts, but typed) ---
    messages = [
        SystemMessage("You are a terse Python tutor. Answer in one sentence."),
        HumanMessage("What's a closure?"),
    ]
    response = model.invoke(messages)
    print("--- Hand-built typed messages ---")
    print(response.content)

    # --- 2) A reusable prompt template, run with different variables ---
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a {persona} assistant. Answer in one sentence."),
            ("human", "{question}"),
        ]
    )
    chain = prompt | model  # LCEL: pipe a template into a model to form a chain

    print("\n--- Same template, different variables ---")
    for persona, question in [
        ("terse", "What's a closure?"),
        ("enthusiastic", "What's a closure?"),
    ]:
        result = chain.invoke({"persona": persona, "question": question})
        print(f"[{persona}] {result.content}")


if __name__ == "__main__":
    main()
