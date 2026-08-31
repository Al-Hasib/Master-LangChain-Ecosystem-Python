"""
Phase 5 - Topic 04: Query Planning

A FIXED decomposition step (structured output, Phase 1 Topic 04's pattern) splits a
compound question into sub-questions, each of which is answered by Topic 03's
multi-tool (vector + SQL + web) agent, then synthesized into one final answer.

Run:
    python code.py
"""

import os
import sqlite3
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

ORDER_ROWS = [
    (1, "Maria Lopez", "Aurora Pro Plan - Annual", 1188.00, "active", "2026-01-15"),
    (2, "Maria Lopez", "Aurora Analytics Add-on", 240.00, "active", "2026-06-02"),
    (3, "James Carter", "Aurora Starter Plan", 348.00, "cancelled", "2026-03-10"),
    (4, "Priya Singh", "Aurora Pro Plan - Annual", 1188.00, "active", "2026-07-21"),
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
        collection_name="aurora_policies_query_planning",
    )
    return store.as_retriever(search_kwargs={"k": 2})


def build_orders_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute(
        "CREATE TABLE orders (id INTEGER, customer_name TEXT, product TEXT, "
        "amount REAL, status TEXT, order_date TEXT)"
    )
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", ORDER_ROWS)
    conn.commit()
    return conn


def build_multi_tool_agent(retriever, db_conn):
    """Same three tools as Topic 03, unchanged - query planning wraps this agent,
    it doesn't replace it."""
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

    @tool
    def query_orders_db(sql_query: str) -> str:
        """Run a read-only SQL SELECT against orders(id, customer_name, product,
        amount, status, order_date). Only SELECT statements are allowed."""
        if not sql_query.strip().lower().startswith("select"):
            return "Error: only SELECT statements are allowed."
        try:
            rows = db_conn.execute(sql_query).fetchall()
        except sqlite3.Error as exc:
            return f"SQL error: {exc}"
        return str(rows) if rows else "No matching rows."

    @tool
    def web_search(query: str) -> str:
        """Search the live web for general knowledge outside Aurora's own data."""
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

    return create_agent(
        model="gpt-4o-mini",
        tools=[search_policies, query_orders_db, web_search],
        system_prompt=(
            "You are Aurora Cloud Analytics' research assistant. Use search_policies "
            "for policy/product questions, query_orders_db for order questions "
            "(write the SQL yourself), and web_search for general knowledge."
        ),
    )


def decompose(planner_model, question: str) -> list[str]:
    """FIXED step: always run, always the same way - not a decision the agent makes."""
    from pydantic import BaseModel, Field

    class SubQuestions(BaseModel):
        """Independent sub-questions that together cover the original question."""

        sub_questions: list[str] = Field(
            description="Independent, non-overlapping sub-questions. If the "
            "original question is already a single, simple question, return a "
            "list containing just that one question unchanged."
        )

    planner = planner_model.with_structured_output(SubQuestions)
    result = planner.invoke(
        f"Decompose this question into independent sub-questions:\n\n{question}"
    )
    return result.sub_questions


def synthesize(model, question: str, sub_answers: list[tuple[str, str]]) -> str:
    labeled = "\n".join(f"Q: {q}\nA: {a}" for q, a in sub_answers)
    prompt = (
        f"Original question: {question}\n\nSub-question/answer pairs:\n{labeled}\n\n"
        "Using ALL of the above, write one coherent final answer that addresses "
        "every part of the original question."
    )
    return model.invoke(prompt).content


def main() -> None:
    require_keys()
    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    retriever = build_retriever()
    db_conn = build_orders_db()
    agent = build_multi_tool_agent(retriever, db_conn)

    question = (
        "What's Aurora's return policy, what's the status of Maria Lopez's most "
        "recent order, and what is LangGraph used for?"
    )

    print(f"Original question: {question}\n")

    sub_questions = decompose(model, question)
    print(f"--- Query plan ({len(sub_questions)} sub-question(s)) ---")
    for i, sub_q in enumerate(sub_questions, 1):
        print(f"  {i}. {sub_q}")

    sub_answers = []
    for sub_q in sub_questions:
        result = agent.invoke({"messages": [{"role": "user", "content": sub_q}]})
        sub_answers.append((sub_q, result["messages"][-1].content))

    print("\n--- Sub-answers ---")
    for sub_q, sub_a in sub_answers:
        print(f"  Q: {sub_q}\n  A: {sub_a}\n")

    final_answer = synthesize(model, question, sub_answers)
    print(f"--- Synthesized final answer ---\n{final_answer}")

    db_conn.close()


if __name__ == "__main__":
    main()
