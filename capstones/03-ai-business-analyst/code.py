"""
Capstone 03: AI Business Analyst (Multi-Agent System)

Run:
    python code.py

Demonstrates: a hand-rolled supervisor pattern (Phase 7 Topic 07) routing a business
question to a Research sub-agent (web search), a SQL sub-agent (in-memory SQLite sales
data), and an Analyst sub-agent (structured-output analysis), then a Report Writer step
synthesizing everything into one written report.
"""

import os
import sqlite3
import sys

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    sys.exit(
        "Missing OPENAI_API_KEY.\n1) cp ../.env.example ../.env\n"
        "2) fill in your key\n3) re-run"
    )

try:
    from langchain.agents import create_agent
    from langchain.chat_models import init_chat_model
    from langchain.tools import tool
    from pydantic import BaseModel, Field
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r ../requirements.txt")


SALES_SCHEMA = (
    "Table `sales(id INTEGER, product TEXT, region TEXT, quarter TEXT, "
    "revenue REAL, units INTEGER)`. Products: 'Nimbus Core', 'Nimbus Pro', "
    "'Nimbus Analytics'. Regions: 'NA', 'EMEA', 'APAC'. Quarters: 'Q1-2026', 'Q2-2026'."
)

SALES_ROWS = [
    ("Nimbus Core", "NA", "Q1-2026", 182000, 910),
    ("Nimbus Core", "NA", "Q2-2026", 201000, 1005),
    ("Nimbus Core", "EMEA", "Q1-2026", 96000, 480),
    ("Nimbus Core", "EMEA", "Q2-2026", 89000, 445),
    ("Nimbus Core", "APAC", "Q1-2026", 54000, 270),
    ("Nimbus Core", "APAC", "Q2-2026", 71000, 355),
    ("Nimbus Pro", "NA", "Q1-2026", 310000, 620),
    ("Nimbus Pro", "NA", "Q2-2026", 298000, 596),
    ("Nimbus Pro", "EMEA", "Q1-2026", 145000, 290),
    ("Nimbus Pro", "EMEA", "Q2-2026", 168000, 336),
    ("Nimbus Pro", "APAC", "Q1-2026", 62000, 124),
    ("Nimbus Pro", "APAC", "Q2-2026", 88000, 176),
    ("Nimbus Analytics", "NA", "Q1-2026", 75000, 150),
    ("Nimbus Analytics", "NA", "Q2-2026", 121000, 242),
    ("Nimbus Analytics", "EMEA", "Q1-2026", 41000, 82),
    ("Nimbus Analytics", "EMEA", "Q2-2026", 58000, 116),
    ("Nimbus Analytics", "APAC", "Q1-2026", 22000, 44),
    ("Nimbus Analytics", "APAC", "Q2-2026", 39000, 78),
]


class SupervisorPlan(BaseModel):
    needs_research: bool = Field(
        description="True if answering this question benefits from external/market "
        "context via web search."
    )
    needs_sql: bool = Field(
        description="True if answering this question requires querying the internal "
        "sales database."
    )
    reason: str = Field(description="One short sentence explaining the routing choice.")


class AnalysisResult(BaseModel):
    key_metrics: list[str] = Field(description="3-5 concrete numbers/facts pulled from the findings.")
    trends: list[str] = Field(description="1-3 patterns visible across the findings.")
    risks: list[str] = Field(description="0-3 risks or concerns worth flagging.")
    recommendation: str = Field(description="One concrete, actionable recommendation.")


def seed_database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE sales (id INTEGER PRIMARY KEY, product TEXT, region TEXT, "
        "quarter TEXT, revenue REAL, units INTEGER)"
    )
    conn.executemany(
        "INSERT INTO sales (product, region, quarter, revenue, units) "
        "VALUES (?, ?, ?, ?, ?)",
        SALES_ROWS,
    )
    conn.commit()
    return conn


def build_sql_agent(model, conn: sqlite3.Connection):
    @tool
    def run_sql(query: str) -> str:
        """Run a read-only SQL SELECT query against the `sales` table and return the
        rows. Only SELECT statements are allowed."""
        cleaned = query.strip().rstrip(";")
        if not cleaned.lower().startswith("select"):
            return "Error: only SELECT statements are allowed."
        try:
            cursor = conn.execute(cleaned)
            rows = cursor.fetchall()
            columns = [d[0] for d in cursor.description]
        except sqlite3.Error as exc:
            return f"SQL error: {exc}"
        if not rows:
            return "Query returned no rows."
        header = ", ".join(columns)
        body = "\n".join(", ".join(str(v) for v in row) for row in rows)
        return f"{header}\n{body}"

    return create_agent(
        model=model,
        tools=[run_sql],
        system_prompt=(
            "You are a SQL analyst. The database has this schema: "
            f"{SALES_SCHEMA}. Write and run SELECT queries with run_sql to answer the "
            "question, then summarize the numeric findings in plain text."
        ),
    )


def build_research_agent(model):
    @tool
    def web_search(query: str) -> str:
        """Search the web for market/industry context (competitors, trends, general
        facts) not available in the internal sales database."""
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
        model=model,
        tools=[web_search],
        system_prompt=(
            "You are a market research analyst. Use web_search to gather relevant "
            "external context for the business question, then summarize findings in "
            "plain text with brief source mentions."
        ),
    )


def run_sub_agent(agent, question: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content


def report_writer(model, question: str, research: str, sql: str, analysis: AnalysisResult) -> str:
    prompt = (
        "Write a concise business report (markdown, a few short sections) answering "
        f"this question for a business stakeholder:\n\n{question}\n\n"
        f"Research findings:\n{research or '(not gathered - not needed for this question)'}\n\n"
        f"SQL findings:\n{sql or '(not gathered - not needed for this question)'}\n\n"
        f"Structured analysis:\n"
        f"- Key metrics: {analysis.key_metrics}\n"
        f"- Trends: {analysis.trends}\n"
        f"- Risks: {analysis.risks}\n"
        f"- Recommendation: {analysis.recommendation}\n\n"
        "Include a short 'Recommendation' section at the end."
    )
    return model.invoke(prompt).content


def analyze_business_question(model, sql_agent, research_agent, question: str) -> str:
    print(f"=== Question: {question} ===")

    # Supervisor step: decide which sub-agents are actually needed.
    planner = model.with_structured_output(SupervisorPlan)
    plan = planner.invoke(
        f"Business question: {question}\nDecide whether Research (web) and/or SQL "
        "(internal sales data) are needed to answer it."
    )
    print(f"  [supervisor] research={plan.needs_research} sql={plan.needs_sql} - {plan.reason}")

    research_findings = run_sub_agent(research_agent, question) if plan.needs_research else ""
    sql_findings = run_sub_agent(sql_agent, question) if plan.needs_sql else ""
    if plan.needs_research:
        print(f"  [research] {research_findings[:150]}...")
    if plan.needs_sql:
        print(f"  [sql] {sql_findings[:150]}...")

    # Analyst step: always runs, over whatever was gathered.
    analyst = model.with_structured_output(AnalysisResult)
    combined = f"Research:\n{research_findings}\n\nSQL:\n{sql_findings}"
    analysis = analyst.invoke(
        f"Question: {question}\n\nFindings:\n{combined}\n\nAnalyze these findings."
    )
    print(f"  [analyst] metrics={analysis.key_metrics}")

    report = report_writer(model, question, research_findings, sql_findings, analysis)
    print(f"  [report]\n{report}\n")
    return report


def main() -> None:
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    conn = seed_database()
    sql_agent = build_sql_agent(model, conn)
    research_agent = build_research_agent(model)

    questions = [
        "How did Nimbus Analytics revenue change from Q1 to Q2 2026 across regions, "
        "and is that growth consistent with broader industry trends in analytics "
        "tooling?",
        "Which product had the highest total revenue in Q2 2026?",
    ]
    for question in questions:
        analyze_business_question(model, sql_agent, research_agent, question)

    conn.close()


if __name__ == "__main__":
    main()
