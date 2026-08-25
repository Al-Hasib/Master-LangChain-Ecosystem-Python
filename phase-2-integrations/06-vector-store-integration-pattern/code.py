"""
Phase 2 - Topic 06: Vector Store Integration Pattern

Same documents, same embeddings, two backends (Chroma and FAISS) - identical
.from_documents() / .similarity_search() calls either way.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

DOCS_TEXT = [
    "The company's return policy allows returns within 30 days of purchase.",
    "Support hours are 9am-6pm, Monday through Friday.",
    "Premium plan subscribers get free shipping on all orders.",
    "Refunds are processed within 5 business days.",
]
QUERY = "How long do refunds take?"


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )
    try:
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    documents = [Document(page_content=text) for text in DOCS_TEXT]

    # --- Chroma ---
    try:
        from langchain_chroma import Chroma

        chroma_store = Chroma.from_documents(documents, embedding=embeddings)
        results = chroma_store.similarity_search(QUERY, k=2)
        print("[chroma] top matches:")
        for doc in results:
            print(f"  - {doc.page_content}")
    except ImportError:
        print("[skipped] chroma: run `pip install langchain-chroma`")

    # --- FAISS ---
    try:
        from langchain_community.vectorstores import FAISS

        faiss_store = FAISS.from_documents(documents, embedding=embeddings)
        results = faiss_store.similarity_search(QUERY, k=2)
        print("\n[faiss] top matches (SAME calls, different backend):")
        for doc in results:
            print(f"  - {doc.page_content}")
    except ImportError:
        print("[skipped] faiss: run `pip install faiss-cpu`")


if __name__ == "__main__":
    main()
