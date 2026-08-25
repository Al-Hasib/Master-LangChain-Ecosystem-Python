"""
Phase 4 - Topic 01: Naive RAG vs Production RAG

Runs Phase 3's naive top-k pipeline (embed -> similarity_search -> stuff -> generate)
against a query whose answer is fragmented across chunks, and shows the pipeline
confidently give a wrong answer because the overriding fact never made top-k.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# A small "Nimbus" (fictional SaaS) knowledge base. Reused/extended across this phase.
# Note: the refund EXCEPTION for the Apollo plan (doc index 3) deliberately avoids the
# words "refund" and "Apollo" together, and instead talks about "enterprise annual
# contracts" - mimicking how real docs phrase overrides differently from the rules
# they override. That phrasing gap is *why* naive similarity search misses it.
NIMBUS_DOCS = [
    "Nimbus Standard and Pro plans include a 30-day money-back guarantee. "
    "Refund requests are filed through the Billing dashboard.",
    "The Apollo plan is Nimbus's enterprise tier: a dedicated account manager, "
    "a 600 requests/minute API limit, and priority onboarding.",
    "Nimbus API rate limits are 60 requests/minute on Standard plans and "
    "600 requests/minute on Apollo plans.",
    # <-- the fact that actually answers the eligibility question:
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

# Index of the doc that actually contains the answer-changing fact (for the demo print).
MISSING_FACT_INDEX = 3

QUERY = "I'm on the Apollo plan and want a refund - am I eligible?"


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def main() -> None:
    require_openai_key()
    try:
        from langchain.chat_models import init_chat_model
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    documents = [Document(page_content=text, metadata={"id": i}) for i, text in enumerate(NIMBUS_DOCS)]

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(documents, embedding=embeddings)

    # --- The naive pipeline, exactly as Phase 3 built it ---
    k = 2
    retrieved = vectorstore.similarity_search(QUERY, k=k)

    context = "\n\n".join(doc.page_content for doc in retrieved)
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    prompt = (
        "Answer the question using ONLY the context below. "
        "If the context doesn't fully answer it, say so.\n\n"
        f"Context:\n{context}\n\nQuestion: {QUERY}"
    )
    answer = model.invoke(prompt).content

    print(f"Query: {QUERY}\n")
    print(f"--- Naive retrieval (k={k}) ---")
    for doc in retrieved:
        print(f"  [doc {doc.metadata['id']}] {doc.page_content}")

    print(f"\n--- Generated answer ---\n{answer}")

    # Did the fragment with the actual override fact make it into top-k?
    retrieved_ids = {doc.metadata["id"] for doc in retrieved}
    print("\n--- What naive retrieval missed ---")
    if MISSING_FACT_INDEX in retrieved_ids:
        print("(this run happened to retrieve the override fact - re-run or lower k to reproduce the gap)")
    else:
        print(f"  [doc {MISSING_FACT_INDEX}] {NIMBUS_DOCS[MISSING_FACT_INDEX]}")
        print(
            "\nThis chunk never made top-k because it doesn't say 'refund' or 'Apollo' - "
            "it talks about 'enterprise annual contracts' and a 'Master Services Agreement.' "
            "The model above answered faithfully from what it was given; what it was given "
            "was incomplete. That's a retrieval failure, not a generation failure - see "
            "Topics 02-05 for the fixes."
        )


if __name__ == "__main__":
    main()
