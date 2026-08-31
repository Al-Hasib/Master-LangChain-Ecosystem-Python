"""
Phase 5 - Topic 01: What is Agentic RAG?

Same knowledge base, two shapes:
  1) Fixed RAG workflow - ALWAYS retrieve, then generate (Phase 3-4 style).
  2) Agent-directed retrieval - a create_agent loop decides whether to retrieve.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# A tiny in-code knowledge base standing in for Aurora Cloud Analytics' internal docs.
# Real code would load these via Phase 3's loaders; here we build Documents directly so
# the topic runs standalone with no external files.
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
    """Same Qdrant pattern as Phase 0 Topic 06 - documents in, retriever out."""
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings
    from langchain_qdrant import QdrantVectorStore

    documents = [Document(page_content=text) for text in KNOWLEDGE_BASE]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    store = QdrantVectorStore.from_documents(
        documents,
        embedding=embeddings,
        location=":memory:",
        collection_name="aurora_policies_agentic_rag_intro",
    )
    return store.as_retriever(search_kwargs={"k": 2})


def fixed_rag_workflow(model, retriever, question: str) -> str:
    """Workflow shape: retrieval ALWAYS happens, no matter the question."""
    docs = retriever.invoke(question)
    context = "\n".join(doc.page_content for doc in docs)
    prompt = (
        "Answer using ONLY the context below. If the context doesn't contain the "
        f"answer, say so.\n\nContext:\n{context}\n\nQuestion: {question}"
    )
    response = model.invoke(prompt)
    return f"[retrieved {len(docs)} doc(s)] {response.content}"


def main() -> None:
    require_keys()
    try:
        from langchain.agents import create_agent
        from langchain.chat_models import init_chat_model
        from langchain.tools import tool
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    retriever = build_retriever()

    # --- Agent-directed shape: retrieval is a TOOL, not a forced step ---
    @tool
    def search_policies(query: str) -> str:
        """Search Aurora Cloud Analytics' internal policy knowledge base (returns,
        support hours, data exports, plan features). Only use this for questions
        about Aurora's own policies/product - NOT for general knowledge or math."""
        docs = retriever.invoke(query)
        return "\n".join(doc.page_content for doc in docs)

    agent = create_agent(
        model=model,
        tools=[search_policies],
        system_prompt=(
            "You are a helpful assistant for Aurora Cloud Analytics. Call "
            "search_policies only when the question is about Aurora's own policies "
            "or product. Answer everything else directly, without calling it."
        ),
    )

    questions = [
        "What's Aurora's return policy?",
        "What's 12 times 7?",  # doesn't need the knowledge base at all
    ]

    for question in questions:
        print(f"\n=== Question: {question} ===")

        fixed_answer = fixed_rag_workflow(model, retriever, question)
        print(f"  Fixed RAG workflow:   {fixed_answer}")

        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        called_tool = any(getattr(m, "tool_calls", None) for m in result["messages"])
        tag = "retrieved via agent decision" if called_tool else "no retrieval"
        print(f"  Agent-directed:       [{tag}] {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
