"""
Phase 4 - Topic 02: Query Transformation Techniques

Re-runs Topic 01's Apollo refund query four ways - naive, rewritten, multi-query,
and HyDE - and checks which technique(s) retrieve the override-fact document that
naive top-k search missed.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Same Nimbus knowledge base as Topic 01.
NIMBUS_DOCS = [
    "Nimbus Standard and Pro plans include a 30-day money-back guarantee. "
    "Refund requests are filed through the Billing dashboard.",
    "The Apollo plan is Nimbus's enterprise tier: a dedicated account manager, "
    "a 600 requests/minute API limit, and priority onboarding.",
    "Nimbus API rate limits are 60 requests/minute on Standard plans and "
    "600 requests/minute on Apollo plans.",
    "Annual enterprise contracts signed under Nimbus's Master Services Agreement "
    "are final sale once the account is provisioned; the standard 30-day refund "
    "window does not apply to them. Exceptions require account-manager approval.",
    "Password resets are self-service via the login page's 'Forgot password' link; "
    "the reset link expires after 15 minutes.",
    "Support response times: Standard plan gets email support within 2 business days. "
    "Apollo plan gets a 1-hour SLA via a dedicated Slack channel.",
    "Nimbus's onboarding checklist for new engineers includes VPN setup, repo access "
    "requests, and a 2-week shadow period.",
]

MISSING_FACT_INDEX = 3
QUERY = "I'm on the Apollo plan and want a refund - am I eligible?"


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def report(label: str, retrieved_ids: set) -> None:
    hit = MISSING_FACT_INDEX in retrieved_ids
    mark = "FOUND" if hit else "missed"
    print(f"  [{mark}] {label} -> retrieved doc ids {sorted(retrieved_ids)}")


def main() -> None:
    require_openai_key()
    try:
        from langchain.chat_models import init_chat_model
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    try:
        # MultiQueryRetriever moved out of the core `langchain` package in the v1
        # reorganization - it now lives in the separate `langchain-classic` package.
        # pip install langchain-classic  (not yet in requirements.txt - see doc.md)
        from langchain_classic.retrievers.multi_query import MultiQueryRetriever
    except ImportError:
        sys.exit(
            "Missing dependency. Run: pip install -r ../../requirements.txt langchain-classic"
        )

    documents = [Document(page_content=text, metadata={"id": i}) for i, text in enumerate(NIMBUS_DOCS)]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(documents, embedding=embeddings)
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    print(f"Query: {QUERY}\n")

    # --- Baseline: naive top-k on the raw query (Topic 01) ---
    naive_docs = vectorstore.similarity_search(QUERY, k=2)
    report("Naive (raw query, k=2)", {d.metadata["id"] for d in naive_docs})

    # --- 1) Query rewriting: LLM expands the query before searching ---
    rewrite_prompt = (
        "Rewrite the following user question into a more explicit search query for a "
        "vector database. Name the entities involved and add likely synonyms. "
        "Return ONLY the rewritten query, no explanation.\n\n"
        f"Question: {QUERY}"
    )
    rewritten_query = model.invoke(rewrite_prompt).content.strip()
    rewritten_docs = vectorstore.similarity_search(rewritten_query, k=2)
    report(f"Rewritten query ('{rewritten_query[:60]}...')", {d.metadata["id"] for d in rewritten_docs})

    # --- 2) Multi-query retrieval: N variants, union of results ---
    mq_retriever = MultiQueryRetriever.from_llm(
        retriever=vectorstore.as_retriever(search_kwargs={"k": 2}), llm=model
    )
    mq_docs = mq_retriever.invoke(QUERY)
    report("Multi-query retrieval (union of variants)", {d.metadata["id"] for d in mq_docs})

    # --- 3) HyDE: embed a hypothetical answer instead of the query ---
    hyde_prompt = (
        "Write a short, generic hypothetical answer paragraph to the following question, "
        "as if it appeared in a company's internal policy docs. It's OK if details are "
        "invented - this is only used to guide document search, not shown to a user.\n\n"
        f"Question: {QUERY}"
    )
    hypothetical_answer = model.invoke(hyde_prompt).content
    hyde_docs = vectorstore.similarity_search(hypothetical_answer, k=2)
    report("HyDE (embed hypothetical answer)", {d.metadata["id"] for d in hyde_docs})

    print(f"\nThe override fact lives in doc {MISSING_FACT_INDEX}:")
    print(f"  {NIMBUS_DOCS[MISSING_FACT_INDEX]}")


if __name__ == "__main__":
    main()
