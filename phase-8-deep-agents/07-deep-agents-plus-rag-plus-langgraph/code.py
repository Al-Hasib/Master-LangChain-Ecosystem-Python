"""
Phase 8 - Topic 07: Deep Agents + RAG / + LangGraph

Run:
    python code.py

Shows a retriever as "just another tool" in a deep agent's tools= list, reusing the
small in-code Chroma pattern from Phase 0 Topic 06 / Phase 2 Topic 06. The LangGraph
composition (embedding a deep agent as one node in a larger StateGraph) is left as an
illustrative comment - Phase 6 owns real LangGraph code.
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
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    try:
        from deepagents import create_deep_agent
    except ImportError:
        sys.exit("Missing dependency. Run: pip install deepagents")

    model = init_chat_model("gpt-4o-mini", model_provider="openai")

    # --- Small in-code Chroma knowledge base (Phase 0 Topic 06 / Phase 2 Topic 06 pattern) ---
    docs_text = [
        "Our return policy allows returns within 30 days of purchase.",
        "Premium plan subscribers get free shipping on all orders.",
        "Refunds are processed within 5 business days.",
    ]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    documents = [Document(page_content=text) for text in docs_text]
    vector_store = Chroma.from_documents(documents, embedding=embeddings)

    @tool
    def search_knowledge_base(query: str) -> str:
        """Search the internal company knowledge base (returns/shipping policy)."""
        results = vector_store.similarity_search(query, k=2)
        return "\n".join(f"- {doc.page_content}" for doc in results)

    agent = create_deep_agent(
        model=model,
        tools=[search_knowledge_base],
        system_prompt=(
            "You answer questions about company policy. Use search_knowledge_base "
            "for anything about returns, refunds, or shipping."
        ),
    )

    question = "How long do refunds take to process?"
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    tools_called = [
        call["name"]
        for message in result["messages"]
        for call in (getattr(message, "tool_calls", []) or [])
    ]
    print(f"Tool(s) chosen by the agent: {tools_called}")
    print(f"Final answer: {result['messages'][-1].content}")

    # --- Illustrative only: embedding this same deep agent as one LangGraph node ---
    print(
        "\n--- Deep agent + LangGraph (illustrative - Phase 6 owns real graph code) ---\n"
        "# def deep_agent_node(state):\n"
        "#     result = agent.invoke({'messages': state['messages']})\n"
        "#     return {'messages': result['messages']}\n"
        "#\n"
        "# graph.add_node('research', deep_agent_node)  # the deep agent IS one node"
    )


if __name__ == "__main__":
    main()
