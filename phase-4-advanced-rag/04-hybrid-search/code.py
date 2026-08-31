"""
Phase 4 - Topic 04: Hybrid Search

Compares BM25 (keyword) vs dense vector search vs an EnsembleRetriever hybrid of the
two, on a query containing an exact error code that dense embeddings underserve.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Nimbus support docs, including one that references an exact error code. Dense
# embeddings represent MEANING, not exact tokens, so "ERR_RL429" doesn't stand out
# much in embedding space - but it's an exact keyword match for BM25.
NIMBUS_DOCS = [
    "ERR_RL429 means your account has exceeded its API rate limit. Wait for the "
    "window to reset, or upgrade to the Apollo plan for a higher 600 req/min ceiling.",
    "Nimbus API rate limits are 60 requests/minute on Standard plans and "
    "600 requests/minute on Apollo plans.",
    "If you're being throttled repeatedly, batch your requests or use the bulk "
    "endpoint instead of looping individual calls.",
    "Support response times: Standard plan gets email support within 2 business days. "
    "Apollo plan gets a 1-hour SLA via a dedicated Slack channel.",
    "Password resets are self-service via the login page's 'Forgot password' link; "
    "the reset link expires after 15 minutes.",
    "Nimbus's onboarding checklist for new engineers includes VPN setup, repo access "
    "requests, and a 2-week shadow period.",
]

QUERY = "How do I fix ERR_RL429?"


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def show(label: str, docs) -> None:
    print(f"\n--- {label} ---")
    for rank, doc in enumerate(docs, start=1):
        print(f"  {rank}. [doc {doc.metadata.get('id', '?')}] {doc.page_content[:70]}...")


def main() -> None:
    require_openai_key()
    try:
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
        from langchain_qdrant import QdrantVectorStore
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    try:
        # BM25Retriever lives in langchain_community (not core langchain), and needs
        # the rank_bm25 package installed for its scoring backend.
        # pip install langchain-community rank_bm25  (not yet in requirements.txt - see doc.md)
        from langchain_community.retrievers import BM25Retriever
    except ImportError:
        sys.exit(
            "Missing dependency. Run: "
            "pip install -r ../../requirements.txt langchain-community rank_bm25"
        )

    try:
        # EnsembleRetriever moved to langchain-classic in the langchain v1 reorganization.
        # pip install langchain-classic  (not yet in requirements.txt - see doc.md)
        from langchain_classic.retrievers import EnsembleRetriever
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt langchain-classic")

    documents = [Document(page_content=text, metadata={"id": i}) for i, text in enumerate(NIMBUS_DOCS)]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = QdrantVectorStore.from_documents(
        documents, embedding=embeddings, location=":memory:", collection_name="phase4_hybrid_search"
    )

    print(f"Query: {QUERY}")

    # --- Vector search alone ---
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    show("Vector search alone (semantic)", vector_retriever.invoke(QUERY))

    # --- BM25 alone ---
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = 3
    show("BM25 alone (keyword)", bm25_retriever.invoke(QUERY))

    # --- Hybrid: EnsembleRetriever fuses both ranked lists (Reciprocal Rank Fusion) ---
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5]
    )
    show("Hybrid (BM25 + vector, EnsembleRetriever)", hybrid_retriever.invoke(QUERY))

    print(
        "\nThe error-code document (doc 0) is an exact keyword match for 'ERR_RL429' - "
        "BM25 ranks it highly by construction. Vector search may rank it lower, since "
        "the code itself carries little semantic meaning. Hybrid search keeps it near "
        "the top regardless, because it counts a strong rank from EITHER retriever."
    )


if __name__ == "__main__":
    main()
