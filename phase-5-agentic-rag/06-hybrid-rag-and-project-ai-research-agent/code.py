"""
Phase 5 - Topic 06 (Phase Project): Hybrid RAG & AI Research Agent

    User -> Query Planning (FIXED) -> Agent -> {Web, Vector, SQL, APIs} (AGENT-DIRECTED)
                                                          -> Groundedness check -> Answer

Combines every prior Phase 5 topic into one system: a fixed query-planning step
(Topic 04) always runs first, an agent (Topic 03) decides which of four tools to call
per sub-question, and a groundedness check (Topic 05) validates the synthesized answer
before it's returned - retrying the whole plan-and-answer pass once if it fails.

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

# Fixed lookup table standing in for a real FX-rates REST API - deterministic so the
# demo runs with no extra API key, same idea as Phase 1 Topic 11's date/time tool.
EXCHANGE_RATES = {("USD", "EUR"): 0.92, ("USD", "GBP"): 0.79, ("EUR", "USD"): 1.09}


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
        collection_name="aurora_policies_hybrid_rag",
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


def build_research_agent(retriever, db_conn):
    """Four knowledge-source tools - Web, Vector, SQL, APIs - on one agent, exactly
    the phase-project diagram in README.md."""
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

    @tool
    def get_exchange_rate(base_currency: str, target_currency: str) -> str:
        """Get the exchange rate between two ISO currency codes (e.g. 'USD', 'EUR').
        In production this would call a real FX-rates REST API; here it's a fixed
        lookup so the demo runs without an extra API key."""
        rate = EXCHANGE_RATES.get((base_currency.upper(), target_currency.upper()))
        if rate is None:
            return f"No rate available for {base_currency}->{target_currency}."
        return f"1 {base_currency.upper()} = {rate} {target_currency.upper()}"

    return create_agent(
        model="gpt-4o-mini",
        tools=[search_policies, query_orders_db, web_search, get_exchange_rate],
        system_prompt=(
            "You are Aurora Cloud Analytics' research assistant. Use search_policies "
            "for policy/product questions, query_orders_db for order questions "
            "(write the SQL yourself), web_search for general knowledge, and "
            "get_exchange_rate for currency conversion questions. Call as many "
            "tools as needed before giving your final answer."
        ),
    )


def decompose(planner_model, question: str) -> list[str]:
    """FIXED step (Topic 04) - always runs, always the same way."""
    from pydantic import BaseModel, Field

    class SubQuestions(BaseModel):
        """Independent sub-questions that together cover the original question."""

        sub_questions: list[str] = Field(
            description="Independent, non-overlapping sub-questions. If the "
            "original question is already simple, return a list of just that one."
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


def check_groundedness(model, question: str, context: str, answer: str):
    from pydantic import BaseModel, Field

    class GroundednessCheck(BaseModel):
        """Whether an answer is fully supported by the gathered context."""

        grounded: bool = Field(
            description="True only if every claim in the answer is directly "
            "supported by the context. False if it states anything the context "
            "doesn't back up."
        )
        reasoning: str = Field(description="One short sentence explaining the verdict.")

    grader = model.with_structured_output(GroundednessCheck)
    prompt = (
        f"Question: {question}\n\nGathered context (from all sub-questions):\n"
        f"{context}\n\nFinal answer given: {answer}\n\n"
        "Is the final answer fully grounded in the gathered context?"
    )
    return grader.invoke(prompt)


def run_research_agent(model, agent, question: str) -> tuple[str, str]:
    """One full pass: plan -> answer each sub-question -> synthesize. Returns the
    synthesized answer and the concatenated context gathered along the way."""
    sub_questions = decompose(model, question)
    print(f"  Query plan: {sub_questions}")

    sub_answers = []
    all_context = []
    for sub_q in sub_questions:
        result = agent.invoke({"messages": [{"role": "user", "content": sub_q}]})
        tool_context = [
            m.content for m in result["messages"] if type(m).__name__ == "ToolMessage"
        ]
        all_context.extend(tool_context)
        sub_answers.append((sub_q, result["messages"][-1].content))

    answer = synthesize(model, question, sub_answers)
    context = "\n".join(all_context) if all_context else "(no tools were called)"
    return answer, context


def main() -> None:
    require_keys()
    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    retriever = build_retriever()
    db_conn = build_orders_db()
    agent = build_research_agent(retriever, db_conn)

    # A four-part question that needs all four tools: vector, SQL, web, and API.
    question = (
        "What's Aurora's return policy, what's the status of Maria Lopez's most "
        "recent order, what is LangGraph used for, and what's the exchange rate "
        "from USD to EUR?"
    )

    print(f"Question: {question}\n")
    print("--- Pass 1 ---")
    answer, context = run_research_agent(model, agent, question)
    verdict = check_groundedness(model, question, context, answer)
    print(f"  Answer: {answer}")
    print(f"  Grounded: {verdict.grounded} ({verdict.reasoning})")

    if not verdict.grounded:
        print("\n--- Retry pass (groundedness check failed) ---")
        answer, context = run_research_agent(model, agent, question)
        verdict = check_groundedness(model, question, context, answer)
        print(f"  Answer: {answer}")
        print(f"  Grounded: {verdict.grounded} ({verdict.reasoning})")

    print(f"\nFinal answer:\n{answer}")

    db_conn.close()


if __name__ == "__main__":
    main()
