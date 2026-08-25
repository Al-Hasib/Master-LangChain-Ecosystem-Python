"""
Phase 6 - Topic 11 (Project): Agentic RAG with LangGraph

Run:
    python code.py

Builds a small in-code Chroma knowledge base, then wires an explicit graph:
retrieve -> grade_documents -> (generate | rewrite_query loop back to retrieve).
Mirrors Phase 5's agentic RAG agent loop as an inspectable graph instead.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

MAX_REWRITES = 2


def require_keys() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def main() -> None:
    require_keys()
    try:
        from typing_extensions import TypedDict

        from langchain_core.documents import Document
        from langchain.chat_models import init_chat_model
        from langchain_chroma import Chroma
        from langchain_openai import OpenAIEmbeddings
        from langgraph.graph import StateGraph, START, END
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # --- small in-code knowledge base (Phase 3 Topic 05's retriever pattern) ---
    knowledge_base = [
        "Nimbus Cloud Storage's Starter plan costs $5/month for 100GB and includes "
        "email support with a 48-hour response time.",
        "Nimbus Cloud Storage's Pro plan costs $15/month for 2TB and includes priority "
        "chat support with a 4-hour response time.",
        "All Nimbus Cloud Storage plans use AES-256 encryption at rest and TLS 1.3 "
        "in transit; encryption keys are rotated every 90 days.",
        "Nimbus Cloud Storage sync typically completes within 30 seconds for files "
        "under 50MB on a broadband connection.",
        "Nimbus Cloud Storage support is available Monday-Friday, 9am-6pm UTC, "
        "excluding public holidays.",
    ]
    documents = [Document(page_content=text) for text in knowledge_base]

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma.from_documents(documents, embedding=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 2})

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    class State(TypedDict):
        question: str
        documents: list
        grade: str
        generation: str
        rewrite_count: int

    def retrieve(state: State) -> dict:
        docs = retriever.invoke(state["question"])
        return {"documents": [d.page_content for d in docs]}

    def grade_documents(state: State) -> dict:
        """The step that's invisible inside a plain agent loop: a dedicated,
        inspectable relevance check."""
        joined = "\n".join(f"- {d}" for d in state["documents"])
        prompt = (
            "Do the following retrieved passages contain enough information to "
            f"answer the question {state['question']!r}? Passages:\n{joined}\n\n"
            "Reply with only 'yes' or 'no'."
        )
        raw = model.invoke(prompt).content.strip().lower()
        return {"grade": "yes" if raw.startswith("yes") else "no"}

    def route_after_grading(state: State) -> str:
        if state["grade"] == "yes" or state["rewrite_count"] >= MAX_REWRITES:
            return "generate"
        return "rewrite_query"

    def rewrite_query(state: State) -> dict:
        prompt = (
            "This search query didn't retrieve a good enough answer: "
            f"{state['question']!r}. Rewrite it as a clearer, more specific "
            "search query. Reply with only the rewritten query."
        )
        rewritten = model.invoke(prompt).content.strip()
        return {"question": rewritten, "rewrite_count": state["rewrite_count"] + 1}

    def generate(state: State) -> dict:
        joined = "\n".join(f"- {d}" for d in state["documents"])
        prompt = (
            f"Answer the question using ONLY these passages. Question: "
            f"{state['question']!r}\nPassages:\n{joined}\n\n"
            "If the passages don't contain the answer, say so plainly."
        )
        return {"generation": model.invoke(prompt).content}

    builder = StateGraph(State)
    builder.add_node("retrieve", retrieve)
    builder.add_node("grade_documents", grade_documents)
    builder.add_node("rewrite_query", rewrite_query)
    builder.add_node("generate", generate)

    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "grade_documents")
    builder.add_conditional_edges(
        "grade_documents",
        route_after_grading,
        {"generate": "generate", "rewrite_query": "rewrite_query"},
    )
    builder.add_edge("rewrite_query", "retrieve")  # loop back
    builder.add_edge("generate", END)

    graph = builder.compile()

    questions = [
        "How much does the Pro plan cost and how fast is support?",
        "Tell me about it.",  # deliberately vague - expected to trigger a rewrite
    ]

    for question in questions:
        print(f"--- question: {question!r} ---")
        result = graph.invoke({"question": question, "rewrite_count": 0})
        if result["question"] != question:
            print(f"  rewritten query: {result['question']!r} (after {result['rewrite_count']} rewrite(s))")
        print(f"  answer: {result['generation']}\n")


if __name__ == "__main__":
    main()
