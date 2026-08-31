"""
Phase 3 - Topic 05: Retrievers & Similarity Search

Wraps the same Qdrant store as a Retriever two ways - fixed top-k, and
score-threshold - and runs the same query through both .invoke() calls to compare
result counts and behavior.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

CORPUS = [
    "Northwind Outfitters accepts returns within 30 days of purchase with a valid receipt.",
    "Refunds are processed within 5-7 business days after the returned item is received.",
    "Premium members get free standard shipping on all orders over $50.",
    "Customer support is available 9am-6pm Eastern Time, Monday through Friday.",
    "The TrailBlazer 40L backpack has a lifetime warranty against manufacturing defects.",
]

QUERY = "How long do refunds take?"


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )
    try:
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
        from langchain_qdrant import QdrantVectorStore
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    documents = [Document(page_content=text) for text in CORPUS]
    vector_store = QdrantVectorStore.from_documents(
        documents,
        embedding=embeddings,
        location=":memory:",
        collection_name="phase3_topic05_retrievers",
    )

    # --- Mode 1: fixed top-k - ALWAYS returns exactly k results ---
    topk_retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    topk_results = topk_retriever.invoke(QUERY)

    # --- Mode 2: score threshold - returns 0..N results, whatever clears the bar ---
    threshold_retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.5},
    )
    threshold_results = threshold_retriever.invoke(QUERY)

    print(f"Query: {QUERY!r}\n")

    print(f"[top-k, k=3] {len(topk_results)} result(s) - always exactly 3:")
    for doc in topk_results:
        print(f"  - {doc.page_content}")

    print(f"\n[score_threshold=0.5] {len(threshold_results)} result(s) - only what clears the bar:")
    for doc in threshold_results:
        print(f"  - {doc.page_content}")

    if not threshold_results:
        print("  (empty - no result cleared the threshold; handle this case explicitly)")


if __name__ == "__main__":
    main()
