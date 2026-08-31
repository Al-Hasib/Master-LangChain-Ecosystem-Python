"""
Phase 5 - Topic 05: Retrieval & Answer Validation (Self-Corrective RAG)

After the agent answers, a second LLM call grades whether the retrieved context
actually supports the answer. On a failed grade, the query is refined and the agent
gets ONE retry before the result is reported either way.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Deliberately narrow knowledge base - the export-formats doc mentions CSV/JSON/Parquet
# but says NOTHING about Excel, which is exactly the gap this topic is built to catch.
KNOWLEDGE_BASE = [
    "Aurora Cloud Analytics offers a 30-day return policy on annual plan purchases; "
    "monthly plans are non-refundable after 7 days.",
    "Support hours are 9am-6pm Eastern Time, Monday through Friday. Premium plan "
    "subscribers get 24/7 priority support.",
    "The platform supports data exports in CSV, JSON, and Parquet formats.",
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
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings
    from langchain_qdrant import QdrantVectorStore

    documents = [Document(page_content=text) for text in KNOWLEDGE_BASE]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    store = QdrantVectorStore.from_documents(
        documents,
        embedding=embeddings,
        location=":memory:",
        collection_name="aurora_policies_self_corrective",
    )
    return store.as_retriever(search_kwargs={"k": 2})


def build_agent(retriever):
    """Same single-retriever-tool agent as Topic 02."""
    from langchain.agents import create_agent
    from langchain.tools import tool

    try:
        from langchain_core.tools.retriever import create_retriever_tool

        search_policies = create_retriever_tool(
            retriever,
            name="search_policies",
            description="Search Aurora Cloud Analytics' policy knowledge base "
            "(returns, support hours, data exports, plan features).",
        )
    except ImportError:  # fallback - see Topic 02's doc.md

        @tool
        def search_policies(query: str) -> str:
            """Search Aurora Cloud Analytics' policy knowledge base."""
            docs = retriever.invoke(query)
            return "\n".join(doc.page_content for doc in docs)

    return create_agent(
        model="gpt-4o-mini",
        tools=[search_policies],
        system_prompt="You are a helpful assistant for Aurora Cloud Analytics. "
        "Use search_policies for any question about Aurora's own policies/product.",
    )


def run_and_collect_context(agent, question: str) -> tuple[str, str]:
    """Invoke the agent and pull out both the final answer and the raw context any
    tool call(s) returned - the grader needs the RETRIEVED context, not just the
    final answer, to judge groundedness."""
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    context_parts = [
        m.content for m in result["messages"] if type(m).__name__ == "ToolMessage"
    ]
    context = "\n".join(context_parts) if context_parts else "(no tool was called)"
    answer = result["messages"][-1].content
    return answer, context


def check_groundedness(model, question: str, context: str, answer: str):
    from pydantic import BaseModel, Field

    class GroundednessCheck(BaseModel):
        """Whether an answer is fully supported by the retrieved context."""

        grounded: bool = Field(
            description="True only if every claim in the answer is directly and "
            "explicitly supported by the context. False if the answer states "
            "anything the context doesn't say, even if it sounds plausible."
        )
        reasoning: str = Field(description="One short sentence explaining the verdict.")

    grader = model.with_structured_output(GroundednessCheck)
    prompt = (
        f"Question: {question}\n\nRetrieved context:\n{context}\n\n"
        f"Answer given: {answer}\n\nIs the answer fully grounded in the context?"
    )
    return grader.invoke(prompt)


def refine_query(model, question: str, verdict_reasoning: str) -> str:
    prompt = (
        f"This question wasn't well answered by the first search: {question}\n"
        f"Reason it failed: {verdict_reasoning}\n\n"
        "Rewrite it as a single, more specific search query likely to retrieve the "
        "right document. Reply with ONLY the rewritten query, nothing else."
    )
    return model.invoke(prompt).content.strip()


def main() -> None:
    require_keys()
    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    retriever = build_retriever()
    agent = build_agent(retriever)

    # Excel export isn't in the knowledge base at all - a good setup to see either a
    # correctly-grounded "not supported" answer, or a hallucinated "yes" caught by
    # the grader and retried.
    question = "Does Aurora support exporting data to Excel format?"

    print(f"Question: {question}\n")

    answer, context = run_and_collect_context(agent, question)
    print(f"[attempt 1] Answer:  {answer}")
    print(f"[attempt 1] Context: {context}")

    verdict = check_groundedness(model, question, context, answer)
    print(f"[attempt 1] Grounded: {verdict.grounded} ({verdict.reasoning})")

    if not verdict.grounded:
        refined = refine_query(model, question, verdict.reasoning)
        print(f"\n[retry] Refined query: {refined}")

        answer, context = run_and_collect_context(agent, refined)
        print(f"[retry] Answer:  {answer}")
        print(f"[retry] Context: {context}")

        verdict = check_groundedness(model, question, context, answer)
        print(f"[retry] Grounded: {verdict.grounded} ({verdict.reasoning})")

    print(f"\nFinal reported answer: {answer}")
    print(f"Final groundedness: {verdict.grounded}")


if __name__ == "__main__":
    main()
