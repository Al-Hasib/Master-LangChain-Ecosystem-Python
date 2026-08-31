"""
Phase 3 - Topic 03: Text Splitting & Chunking Strategies

Splits the SAME document two ways (coarse vs. fine chunk_size), embeds each version
into its own Qdrant store, and compares the top retrieval result - showing chunking
choices change retrieval quality, not just chunk count.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# One document mixing five unrelated facts into continuous prose - realistic for a
# handbook page, and exactly the kind of text where chunk size matters.
LONG_DOCUMENT = """Northwind Outfitters Customer Handbook

Returns Policy: Northwind Outfitters accepts returns within 30 days of purchase with a
valid receipt. Items must be unworn and in original packaging. Hiking boots purchased
online can be exchanged in-store within 60 days of the original purchase date.

Refunds: Refunds are processed within 5-7 business days after the returned item is
received at our warehouse. Refunds are issued to the original payment method only, and
gift card purchases are refunded as store credit.

Shipping: Premium members get free standard shipping on all orders over $50. Standard
shipping takes 3-5 business days within the continental US. Express shipping is
available at checkout for an additional fee and arrives in 1-2 business days.

Warranty: The TrailBlazer 40L backpack has a lifetime warranty against manufacturing
defects, covering broken zippers, torn seams, and buckle failures. The warranty does
not cover normal wear and tear or damage from improper use.

Support: Customer support is available 9am-6pm Eastern Time, Monday through Friday.
Support can be reached by phone, live chat, or email, and typically responds to emails
within one business day."""

QUERY = "How long do refunds take?"


def split_and_store(
    text: str, chunk_size: int, chunk_overlap: int, embeddings, collection_name: str
):
    from langchain_core.documents import Document
    from langchain_qdrant import QdrantVectorStore
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents([Document(page_content=text)])
    store = QdrantVectorStore.from_documents(
        chunks,
        embedding=embeddings,
        location=":memory:",
        collection_name=collection_name,
    )
    return chunks, store


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )
    try:
        from langchain_openai import OpenAIEmbeddings
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # --- Coarse: big chunks, no overlap - most facts end up bundled together ---
    coarse_chunks, coarse_store = split_and_store(
        LONG_DOCUMENT, 800, 0, embeddings, "phase3_topic03_coarse"
    )

    # --- Fine: small chunks, some overlap - closer to one fact per chunk ---
    fine_chunks, fine_store = split_and_store(
        LONG_DOCUMENT, 150, 20, embeddings, "phase3_topic03_fine"
    )

    print(f"Coarse split: {len(coarse_chunks)} chunk(s) (chunk_size=800, overlap=0)")
    print(f"Fine split:   {len(fine_chunks)} chunk(s) (chunk_size=150, overlap=20)\n")

    print(f"Query: {QUERY!r}\n")

    coarse_top = coarse_store.similarity_search(QUERY, k=1)[0]
    print("[coarse] top match (likely bundled with unrelated policies):")
    print(f"  {coarse_top.page_content!r}\n")

    fine_top = fine_store.similarity_search(QUERY, k=1)[0]
    print("[fine] top match (should be tightly on-topic):")
    print(f"  {fine_top.page_content!r}")


if __name__ == "__main__":
    main()
