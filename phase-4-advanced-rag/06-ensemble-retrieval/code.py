"""
Phase 4 - Topic 06: Ensemble Retrieval

Fuses THREE retrievers (BM25, small-chunk vector, large-chunk vector) with
EnsembleRetriever - the same Reciprocal Rank Fusion mechanism as Topic 04's hybrid
search, generalized past just "keyword + semantic".

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

RUNBOOK_SECTIONS = [
    "Pre-deploy checks: confirm staging has passed smoke tests and the on-call "
    "engineer has acknowledged the deploy window in #deploys. Deploys outside "
    "business hours require a second engineer's sign-off.",
    "Database migrations run automatically via the Atlas migration tool as part of "
    "the deploy pipeline. If a migration fails, the pipeline halts BEFORE the new "
    "version is promoted. Check the Atlas dashboard for the failure reason - most "
    "failures are lock timeouts from a long-running query on the same table.",
    "Rollback procedure: redeploy the previous image tag from the Releases page. "
    "This does NOT automatically revert database migrations - a rollback after a "
    "migration has run requires manually running the down-migration first.",
    "Post-deploy verification: check the /healthz endpoint and the error-rate "
    "dashboard for 5 minutes. A spike above 2% error rate should trigger an "
    "immediate rollback.",
]

QUERY = "What do I do if a migration fails mid-deploy?"


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def show(label: str, docs) -> None:
    print(f"\n--- {label} ---")
    for rank, doc in enumerate(docs, start=1):
        print(f"  {rank}. {doc.page_content[:65]}...")


def main() -> None:
    require_openai_key()
    try:
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    try:
        from langchain_community.retrievers import BM25Retriever
    except ImportError:
        sys.exit(
            "Missing dependency. Run: "
            "pip install -r ../../requirements.txt langchain-community rank_bm25"
        )

    try:
        from langchain_classic.retrievers import EnsembleRetriever
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt langchain-classic")

    documents = [Document(page_content=text, metadata={"id": i}) for i, text in enumerate(RUNBOOK_SECTIONS)]

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Retriever A: BM25 keyword search over the full sections.
    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = 2

    # Retriever B: vector search over SMALL sub-chunks of each section (precision-tuned).
    small_splitter = RecursiveCharacterTextSplitter(chunk_size=80, chunk_overlap=0)
    small_chunks = small_splitter.split_documents(documents)
    small_vectorstore = Chroma.from_documents(
        small_chunks, embedding=embeddings, collection_name="small_chunks"
    )
    small_retriever = small_vectorstore.as_retriever(search_kwargs={"k": 2})

    # Retriever C: vector search over the full (large) sections (context-tuned).
    large_vectorstore = Chroma.from_documents(
        documents, embedding=embeddings, collection_name="large_chunks"
    )
    large_retriever = large_vectorstore.as_retriever(search_kwargs={"k": 2})

    print(f"Query: {QUERY}")
    show("BM25 alone", bm25_retriever.invoke(QUERY))
    show("Small-chunk vector alone", small_retriever.invoke(QUERY))
    show("Large-chunk vector alone", large_retriever.invoke(QUERY))

    # Fuse all three with Reciprocal Rank Fusion. Weights sum to 1.0; tuned here to
    # trust the large-chunk retriever slightly more since it best preserves context.
    ensemble = EnsembleRetriever(
        retrievers=[bm25_retriever, small_retriever, large_retriever],
        weights=[0.3, 0.3, 0.4],
    )
    show("Ensemble (all three fused via RRF)", ensemble.invoke(QUERY))

    print(
        "\nNote: this is the SAME EnsembleRetriever mechanism as Topic 04's hybrid "
        "search - Topic 04 named one specific pairing (BM25 + dense); here we fuse "
        "three retrievers of different granularities instead."
    )


if __name__ == "__main__":
    main()
