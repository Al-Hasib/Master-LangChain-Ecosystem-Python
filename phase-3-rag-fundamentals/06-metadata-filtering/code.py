"""
Phase 3 - Topic 06: Metadata Filtering

Two products whose descriptions deliberately share vocabulary ("warranty") - shows a
plain similarity search can't tell them apart, but a metadata filter can.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Both products mention "warranty" - similarity alone can't isolate one from the other.
PRODUCT_DOCS = [
    ("The TrailBlazer 40L backpack has a lifetime warranty against manufacturing defects.", "TrailBlazer 40L"),
    ("The TrailBlazer 40L backpack weighs 1.8kg and has 5 external pockets.", "TrailBlazer 40L"),
    ("The SummitPro tent has a 2-year warranty covering pole and fabric defects.", "SummitPro tent"),
    ("The SummitPro tent sleeps up to 4 people and weighs 3.2kg.", "SummitPro tent"),
]

QUERY = "What's the warranty coverage?"


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
        from qdrant_client import models
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    documents = [
        Document(page_content=text, metadata={"product": product})
        for text, product in PRODUCT_DOCS
    ]
    vector_store = QdrantVectorStore.from_documents(
        documents,
        embedding=embeddings,
        location=":memory:",
        collection_name="phase3_topic06_metadata_filtering",
    )

    print(f"Query: {QUERY!r}\n")

    # --- Unfiltered: both products are candidates ---
    unfiltered = vector_store.similarity_search(QUERY, k=2)
    print(f"[unfiltered] top {len(unfiltered)} match(es) across BOTH products:")
    for doc in unfiltered:
        print(f"  - ({doc.metadata['product']}) {doc.page_content}")

    # --- Filtered: only TrailBlazer 40L chunks are eligible, regardless of similarity ---
    trailblazer_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.product", match=models.MatchValue(value="TrailBlazer 40L")
            )
        ]
    )
    filtered = vector_store.similarity_search(QUERY, k=2, filter=trailblazer_filter)
    print(f"\n[filtered: product=TrailBlazer 40L] top {len(filtered)} match(es):")
    for doc in filtered:
        print(f"  - ({doc.metadata['product']}) {doc.page_content}")

    # --- Same filter via the Retriever interface (Topic 05) ---
    summitpro_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.product", match=models.MatchValue(value="SummitPro tent")
            )
        ]
    )
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 2, "filter": summitpro_filter}
    )
    via_retriever = retriever.invoke(QUERY)
    print(f"\n[retriever, filter: product=SummitPro tent] top {len(via_retriever)} match(es):")
    for doc in via_retriever:
        print(f"  - ({doc.metadata['product']}) {doc.page_content}")


if __name__ == "__main__":
    main()
