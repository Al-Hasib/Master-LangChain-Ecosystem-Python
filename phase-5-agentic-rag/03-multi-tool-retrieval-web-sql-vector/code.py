"""
Phase 5 - Topic 03: Multi-Tool Retrieval: Web + SQL + Vector

One agent, three knowledge sources (vector store, SQL database, live web search) -
the agent picks which tool(s) a question needs; nothing in this file dispatches by hand.

Run:
    python code.py
"""

import os
import sqlite3
import sys

from dotenv import load_dotenv

load_dotenv()

# --- Source 1: vector store content (Aurora's policy docs, same as Topics 01-02) ---
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

# --- Source 2: SQL database content (order history) ---
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
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings

    documents = [Document(page_content=text) for text in KNOWLEDGE_BASE]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    store = Chroma.from_documents(documents, embedding=embeddings)
    return store.as_retriever(search_kwargs={"k": 2})


def build_orders_db() -> sqlite3.Connection:
    """In-memory sqlite DB, same manual-Document-free pattern as Phase 2 Topic 04's
    load_sql_manually - here the raw connection is kept alive for the SQL tool to
    query directly instead of being converted to Documents up front."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute(
        "CREATE TABLE orders (id INTEGER, customer_name TEXT, product TEXT, "
        "amount REAL, status TEXT, order_date TEXT)"
    )
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", ORDER_ROWS)
    conn.commit()
    return conn


def build_tools(retriever, db_conn):
    from langchain.tools import tool

    try:
        from langchain_core.tools.retriever import create_retriever_tool

        search_policies = create_retriever_tool(
            retriever,
            name="search_policies",
            description=(
                "Search Aurora Cloud Analytics' internal policy knowledge base "
                "(returns, support hours, data exports, plan features)."
            ),
        )
    except ImportError:  # fallback - see Topic 02's doc.md for details

        @tool
        def search_policies(query: str) -> str:
            """Search Aurora Cloud Analytics' internal policy knowledge base
            (returns, support hours, data exports, plan features)."""
            docs = retriever.invoke(query)
            return "\n".join(doc.page_content for doc in docs)

    # --- SQL tool: model writes the SELECT itself, given the schema in the docstring ---
    @tool
    def query_orders_db(sql_query: str) -> str:
        """Run a read-only SQL SELECT against the `orders` table to answer questions
        about customer orders. Schema: orders(id INTEGER, customer_name TEXT,
        product TEXT, amount REAL, status TEXT, order_date TEXT). Only SELECT
        statements are allowed. Example: "SELECT * FROM orders WHERE
        customer_name = 'Maria Lopez' ORDER BY order_date DESC LIMIT 1"."""
        if not sql_query.strip().lower().startswith("select"):
            return "Error: only SELECT statements are allowed."
        try:
            rows = db_conn.execute(sql_query).fetchall()
        except sqlite3.Error as exc:
            return f"SQL error: {exc}"
        return str(rows) if rows else "No matching rows."

    # --- Web tool: identical DuckDuckGo pattern to Phase 1 Topic 11 ---
    @tool
    def web_search(query: str) -> str:
        """Search the live web for general knowledge not in Aurora's own data
        (e.g. questions about other tools/technologies, current events)."""
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

    return [search_policies, query_orders_db, web_search]


def main() -> None:
    require_keys()
    try:
        from langchain.agents import create_agent
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    retriever = build_retriever()
    db_conn = build_orders_db()
    tools = build_tools(retriever, db_conn)

    agent = create_agent(
        model="gpt-4o-mini",
        tools=tools,
        system_prompt=(
            "You are Aurora Cloud Analytics' research assistant. Use search_policies "
            "for Aurora policy/product questions, query_orders_db for customer order "
            "questions (write the SQL yourself using the schema given), and "
            "web_search for general knowledge outside Aurora's own data. Call as "
            "many tools as needed - a question can need more than one - before "
            "giving your final answer."
        ),
    )

    questions = [
        "What's Aurora's return policy?",  # vector only
        "What is the status of Maria Lopez's most recent order?",  # SQL only
        "What is LangGraph used for?",  # web only
        "What's the status of Maria Lopez's most recent order, and what does "
        "Aurora's return policy say about returning it?",  # SQL + vector
    ]

    for question in questions:
        print(f"\n=== Question: {question} ===")
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        for message in result["messages"]:
            tool_calls = getattr(message, "tool_calls", None)
            if tool_calls:
                names = [c["name"] for c in tool_calls]
                print(f"  [tool call] {names}")
        print(f"  Final answer: {result['messages'][-1].content}")

    db_conn.close()


if __name__ == "__main__":
    main()
