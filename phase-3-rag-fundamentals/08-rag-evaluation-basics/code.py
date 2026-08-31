"""
Phase 3 - Topic 08: RAG Evaluation Basics

A small hand-labeled query/relevant-doc set + a manual precision@k check - no
LangSmith dependency (that's Phase 9). Measures retrieval quality with numbers
instead of eyeballing final answers.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Stable ids so we can label "which document(s) SHOULD this query retrieve".
CORPUS = [
    ("returns-policy", "Northwind Outfitters accepts returns within 30 days of purchase with a valid receipt."),
    ("refunds-timing", "Refunds are processed within 5-7 business days after the returned item is received."),
    ("shipping-policy", "Premium members get free standard shipping on all orders over $50."),
    ("support-hours", "Customer support is available 9am-6pm Eastern Time, Monday through Friday."),
    ("backpack-warranty", "The TrailBlazer 40L backpack has a lifetime warranty against manufacturing defects."),
    ("tent-warranty", "The SummitPro tent has a 2-year warranty covering pole and fabric defects."),
]

# Hand-labeled ground truth: for each query, which doc id(s) count as "relevant".
LABELED_QUERIES = [
    ("How long do I have to return an item?", {"returns-policy"}),
    ("When will I get my money back?", {"refunds-timing"}),
    ("What are your customer service hours?", {"support-hours"}),
    ("What's the warranty on the backpack?", {"backpack-warranty"}),
]

K = 2


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    hits = [doc_id for doc_id in retrieved_ids[:k] if doc_id in relevant_ids]
    return len(hits) / k


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
    documents = [
        Document(page_content=text, metadata={"id": doc_id}) for doc_id, text in CORPUS
    ]
    vector_store = QdrantVectorStore.from_documents(
        documents,
        embedding=embeddings,
        location=":memory:",
        collection_name="phase3_topic08_rag_evaluation",
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": K})

    print(f"Retrieval evaluation (precision@{K}) over {len(LABELED_QUERIES)} labeled query(ies):\n")

    scores = []
    for query, relevant_ids in LABELED_QUERIES:
        retrieved = retriever.invoke(query)
        retrieved_ids = [doc.metadata["id"] for doc in retrieved]
        score = precision_at_k(retrieved_ids, relevant_ids, K)
        scores.append(score)

        print(f"Query: {query!r}")
        print(f"  expected relevant: {relevant_ids}")
        print(f"  retrieved:         {retrieved_ids}")
        print(f"  precision@{K}: {score:.2f}\n")

    average = sum(scores) / len(scores)
    print(f"Overall average precision@{K}: {average:.2f} across {len(scores)} queries")
    print(
        "\n(This is a manual proxy for retrieval quality only - it says nothing about "
        "whether the LLM's final answer used the context well. LangSmith, Phase 9, "
        "covers answer-quality eval with LLM-as-judge and versioned datasets.)"
    )


if __name__ == "__main__":
    main()
