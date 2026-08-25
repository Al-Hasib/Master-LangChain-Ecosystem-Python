"""
Phase 5 - Topic 02: Retriever as a Tool

Wraps a Chroma retriever with create_retriever_tool (verified import path:
langchain_core.tools.retriever) instead of hand-writing the @tool wrapper from
Topic 01, then gives an agent ONLY that tool.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE_BASE = [
    "Aurora Cloud Analytics offers a 30-day return policy on annual plan purchases; "
    "monthly plans are non-refundable after 7 days.",
    "Support hours are 9am-6pm Eastern Time, Monday through Friday. Premium plan "
    "subscribers get 24/7 priority support.",
    "The platform supports data exports in CSV, JSON, and Parquet formats. Excel "
    "(.xlsx) export is not currently supported.",
    "Premium plan subscribers receive a dedicated account manager in addition to "
    "priority support.",
]


def require_keys() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def build_retriever():
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings

    documents = [Document(page_content=text) for text in KNOWLEDGE_BASE]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    store = Chroma.from_documents(documents, embedding=embeddings)
    return store.as_retriever(search_kwargs={"k": 2})


def build_retriever_tool(retriever):
    """The verified, current way to wrap a retriever as a tool. If your LangChain
    version is old enough that this import fails, fall back to a plain @tool
    function calling retriever.invoke(query) directly (see Topic 01's code) - that
    version is guaranteed to work and is arguably clearer for teaching anyway."""
    try:
        from langchain_core.tools.retriever import create_retriever_tool
    except ImportError:
        from langchain.tools import tool

        @tool
        def search_policies(query: str) -> str:
            """Search Aurora Cloud Analytics' internal policy knowledge base
            (returns, support hours, data exports, plan features). Only use this
            for questions about Aurora's own policies/product."""
            docs = retriever.invoke(query)
            return "\n".join(doc.page_content for doc in docs)

        return search_policies

    return create_retriever_tool(
        retriever,
        name="search_policies",
        description=(
            "Search Aurora Cloud Analytics' internal policy knowledge base "
            "(returns, support hours, data exports, plan features). Only use this "
            "for questions about Aurora's own policies/product - NOT for general "
            "knowledge, greetings, or math."
        ),
    )


def main() -> None:
    require_keys()
    try:
        from langchain.agents import create_agent
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    retriever = build_retriever()
    retriever_tool = build_retriever_tool(retriever)

    agent = create_agent(
        model="gpt-4o-mini",
        tools=[retriever_tool],
        system_prompt="You are a helpful assistant for Aurora Cloud Analytics.",
    )

    questions = [
        "Does Aurora support exporting data to Excel?",  # on-topic -> should call it
        "Hi, how are you today?",  # off-topic -> should NOT call it
    ]

    for question in questions:
        print(f"\n=== Question: {question} ===")
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        called_tool = any(getattr(m, "tool_calls", None) for m in result["messages"])
        print(f"  Called search_policies: {called_tool}")
        print(f"  Final answer: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
