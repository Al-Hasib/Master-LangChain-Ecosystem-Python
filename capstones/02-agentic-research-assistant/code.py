"""
Capstone 02: Agentic Research Assistant (Agentic RAG)

Run:
    python code.py

Demonstrates: an agent choosing between a vector-search tool and a web-search tool per
question (Phase 5), a heuristic check for a weak first retrieval, a query-rewrite step
(structured output) when that check fails, and cited final answers.
"""

import os
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
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_core.messages import ToolMessage
    from langchain_openai import OpenAIEmbeddings
    from pydantic import BaseModel, Field
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r ../requirements.txt")


# ---------------------------------------------------------------------------
# In-code internal-engineering corpus - the kind of content a web search would
# never surface, giving the agent a real reason to pick vector_search for some
# questions and web_search for others.
# ---------------------------------------------------------------------------
INTERNAL_DOCS = [
    ("runbook-deploy.md", "NimbusCloud deploys are triggered by merging to main. The "
     "pipeline runs unit tests, a canary deploy to 5% of traffic, then a full rollout "
     "after 15 minutes if error rates stay under 0.5%."),
    ("runbook-incident.md", "Sev-1 incidents page the on-call engineer via PagerDuty and "
     "open a dedicated incident Slack channel automatically. A postmortem is required "
     "within 3 business days of resolution."),
    ("architecture-overview.md", "NimbusCloud's core service is a Python monolith backed "
     "by PostgreSQL, with a Redis cache in front of the read path. Async jobs run "
     "through a Celery worker pool."),
    ("architecture-auth.md", "Authentication uses short-lived JWTs (15 minute expiry) "
     "with a refresh-token rotation scheme. Refresh tokens are stored hashed in "
     "PostgreSQL and revoked on password change."),
    ("api-rate-limits.md", "The public API allows 100 requests per minute per API key "
     "on the free tier and 2000 requests per minute on the enterprise tier, enforced "
     "via a Redis token-bucket."),
    ("onboarding-eng.md", "New engineers get repo access on day one and are expected to "
     "ship a small first PR within their first week, paired with a mentor from their "
     "team."),
    ("data-model-users.md", "The `users` table has a `plan_tier` enum column "
     "(free/pro/enterprise) and a `created_at` timestamp used for cohort analysis in "
     "the internal analytics dashboard."),
    ("testing-strategy.md", "Unit tests run on every commit; integration tests run "
     "against a docker-compose stack on every PR; a smaller smoke-test suite runs "
     "against staging after every deploy."),
    ("release-versioning.md", "NimbusCloud follows semantic versioning for its public "
     "SDKs. Breaking API changes require a major version bump and a 90-day deprecation "
     "notice to enterprise customers."),
    ("support-escalation.md", "Support tickets tagged 'enterprise' are escalated to the "
     "on-call engineer if unanswered for 2 hours; all other tickets follow a 24-hour "
     "SLA."),
]


class RewrittenQuery(BaseModel):
    rewritten_query: str = Field(
        description="A clearer, more specific rewrite of the original question, aimed "
        "at getting a better retrieval result."
    )
    reason: str = Field(description="One short sentence on what was unclear before.")


def build_vector_store() -> Chroma:
    documents = [
        Document(page_content=text, metadata={"source_name": name})
        for name, text in INTERNAL_DOCS
    ]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma.from_documents(documents, embedding=embeddings)


def build_tools(store: Chroma):
    # Phase 5 Topic 02: wrap a retriever as a tool the agent calls by choice.
    @tool
    def vector_search(query: str) -> str:
        """Search NimbusCloud's internal engineering docs (architecture, runbooks,
        API limits, onboarding, testing). Use this for questions about how OUR
        systems work internally."""
        docs = store.similarity_search(query, k=3)
        if not docs:
            return "No results found in internal knowledge base."
        return "\n".join(
            f"[{doc.metadata['source_name']}] {doc.page_content}" for doc in docs
        )

    # Same DDGS pattern as Phase 1 Topic 11 - no API key required.
    @tool
    def web_search(query: str) -> str:
        """Search the public web. Use this for general/current information NOT about
        NimbusCloud's own internal systems (e.g. industry facts, other companies,
        general technical concepts)."""
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

    return vector_search, web_search


def weak_tool_results(messages) -> bool:
    """Heuristic self-check (Phase 5 Topic 05): flag a retrieval attempt as weak if
    every tool result was empty/near-empty or an explicit 'no results' message."""
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    if not tool_messages:
        return False  # agent answered from its own knowledge - nothing to judge
    for message in tool_messages:
        content = (message.content or "").strip()
        if content and "no results" not in content.lower() and len(content) > 40:
            return False  # at least one tool call returned something substantial
    return True


def rewrite_query(model, question: str) -> str:
    rewriter = model.with_structured_output(RewrittenQuery)
    result = rewriter.invoke(
        f"This question got weak/empty search results: {question!r}\n"
        "Rewrite it to be more specific and more likely to match either internal "
        "engineering docs or a web search, without changing its intent."
    )
    print(f"    [rewrite] {result.reason} -> {result.rewritten_query!r}")
    return result.rewritten_query


def research(agent, model, question: str) -> str:
    print(f"=== Question: {question} ===")
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    if weak_tool_results(result["messages"]):
        print("  First attempt looked weak - rewriting query and retrying once.")
        rewritten = rewrite_query(model, question)
        result = agent.invoke({"messages": [{"role": "user", "content": rewritten}]})

    for message in result["messages"]:
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            names = [c["name"] for c in tool_calls]
            print(f"  tool call(s): {names}")

    answer = result["messages"][-1].content
    print(f"  Answer: {answer}\n")
    return answer


def main() -> None:
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    store = build_vector_store()
    vector_search, web_search = build_tools(store)

    agent = create_agent(
        model=model,
        tools=[vector_search, web_search],
        system_prompt=(
            "You are a research assistant with two tools. Use vector_search for "
            "questions about NimbusCloud's own internal systems. Use web_search for "
            "general or current information not about NimbusCloud internals. Always "
            "cite your source (the [source_name] tag or the search result title) in "
            "your final answer."
        ),
    )

    questions = [
        "How does NimbusCloud roll out a deploy, and what triggers a rollback?",
        "What is Redis commonly used for in backend architectures?",
        "What NimbusCloud rate limit applies to a free-tier API key?",
    ]
    for question in questions:
        research(agent, model, question)


if __name__ == "__main__":
    main()
