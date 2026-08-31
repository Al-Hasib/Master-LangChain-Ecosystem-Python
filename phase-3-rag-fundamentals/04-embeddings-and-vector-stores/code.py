"""
Phase 3 - Topic 04: Embeddings & Vector Stores

Splits a document into chunks, embeds them into a PERSISTED Qdrant store on disk,
then reopens that same store in a fresh QdrantVectorStore(...) call (no re-embedding)
to prove persistence actually works - not just similarity_search on an in-memory store.

Run:
    python code.py
"""

import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DOCUMENT_TEXT = """Northwind Outfitters accepts returns within 30 days of purchase with
a valid receipt. Refunds are processed within 5-7 business days after the returned item
is received. Premium members get free standard shipping on all orders over $50. The
TrailBlazer 40L backpack has a lifetime warranty against manufacturing defects. Customer
support is available 9am-6pm Eastern Time, Monday through Friday."""

QUERY = "What's the warranty on the backpack?"
PERSIST_DIR = str(Path(__file__).parent / "qdrant_db")
COLLECTION_NAME = "phase3_topic04_embeddings"


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
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from qdrant_client import QdrantClient
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    is_first_run = not Path(PERSIST_DIR).exists()

    if is_first_run:
        # --- Build once: split -> embed -> persist to disk ---
        splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=20)
        chunks = splitter.split_documents([Document(page_content=DOCUMENT_TEXT)])
        vector_store = QdrantVectorStore.from_documents(
            chunks,
            embedding=embeddings,
            path=PERSIST_DIR,
            collection_name=COLLECTION_NAME,
        )
        print(f"[first run] embedded {len(chunks)} chunk(s), persisted to {PERSIST_DIR}")
    else:
        # --- Reopen the SAME on-disk store - zero embedding calls for existing data ---
        client = QdrantClient(path=PERSIST_DIR)
        vector_store = QdrantVectorStore(
            client=client, collection_name=COLLECTION_NAME, embedding=embeddings
        )
        count = vector_store.client.count(collection_name=COLLECTION_NAME).count
        print(f"[reopened] found {count} existing chunk(s) at {PERSIST_DIR}, no re-embedding")

    results = vector_store.similarity_search(QUERY, k=1)
    print(f"\nQuery: {QUERY!r}")
    print(f"Top match: {results[0].page_content!r}")

    print(
        f"\n(Re-run this script without deleting {PERSIST_DIR!r} to see the "
        "'reopened' path. Delete the folder to force a fresh embed.)"
    )


if __name__ == "__main__":
    main()
    # Cleanup is intentionally NOT automatic - the whole point of this topic is
    # persistence across runs. Uncomment to reset for a clean from-scratch demo:
    # shutil.rmtree(PERSIST_DIR, ignore_errors=True)
