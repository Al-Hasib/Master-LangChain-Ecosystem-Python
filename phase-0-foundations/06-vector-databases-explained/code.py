"""
Phase 0 - Topic 06: Vector Databases Explained

Uses Chroma (local, embedded, no server) directly - no LangChain yet, so you can see
what a vector database does on its own before Phase 3 wraps it in abstractions.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

SENTENCES = [
    "a dog barking in the yard",
    "a puppy making noise outside",
    "quarterly tax filing deadline",
    "the cat is sleeping on the sofa",
    "annual income tax return submission",
]
METADATAS = [
    {"topic": "animals"},
    {"topic": "animals"},
    {"topic": "finance"},
    {"topic": "animals"},
    {"topic": "finance"},
]
QUERY = "an animal making sounds outside"


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp .env.example .env\n2) fill in your key\n3) re-run"
        )
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key, model_name="text-embedding-3-small"
    )

    # In-memory client for this demo; use chromadb.PersistentClient(path=...) to persist
    # to disk across runs.
    client = chromadb.Client()
    collection = client.create_collection(
        name="phase0_demo", embedding_function=embedding_fn
    )

    collection.add(
        documents=SENTENCES,
        metadatas=METADATAS,
        ids=[f"doc-{i}" for i in range(len(SENTENCES))],
    )

    print("=== Unfiltered search ===")
    results = collection.query(query_texts=[QUERY], n_results=3)
    for doc, distance in zip(results["documents"][0], results["distances"][0]):
        print(f"  distance={distance:.4f}  {doc}")

    print("\n=== Filtered to topic='animals' ===")
    results = collection.query(
        query_texts=[QUERY], n_results=3, where={"topic": "animals"}
    )
    for doc, distance in zip(results["documents"][0], results["distances"][0]):
        print(f"  distance={distance:.4f}  {doc}")


if __name__ == "__main__":
    main()
