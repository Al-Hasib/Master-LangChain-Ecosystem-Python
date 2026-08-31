"""
Phase 0 - Topic 06: Vector Databases Explained

Uses Qdrant (local, embedded, no server) directly - no LangChain yet, so you can see
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

EMBEDDING_MODEL = "text-embedding-3-small"


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp .env.example .env\n2) fill in your key\n3) re-run"
        )
    try:
        from openai import OpenAI
        from qdrant_client import QdrantClient
        from qdrant_client.models import (
            Distance,
            FieldCondition,
            Filter,
            MatchValue,
            PointStruct,
            VectorParams,
        )
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    openai_client = OpenAI(api_key=api_key)

    def embed(texts: list[str]) -> list[list[float]]:
        response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in response.data]

    vectors = embed(SENTENCES)

    # In-memory client for this demo; use QdrantClient(path=...) to persist to disk
    # across runs.
    client = QdrantClient(location=":memory:")
    client.create_collection(
        collection_name="phase0_demo",
        vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
    )

    client.upsert(
        collection_name="phase0_demo",
        points=[
            PointStruct(id=i, vector=vector, payload={"document": sentence, **meta})
            for i, (vector, sentence, meta) in enumerate(
                zip(vectors, SENTENCES, METADATAS)
            )
        ],
    )

    query_vector = embed([QUERY])[0]

    print("=== Unfiltered search ===")
    results = client.query_points(
        collection_name="phase0_demo", query=query_vector, limit=3
    )
    for point in results.points:
        print(f"  score={point.score:.4f}  {point.payload['document']}")

    print("\n=== Filtered to topic='animals' ===")
    results = client.query_points(
        collection_name="phase0_demo",
        query=query_vector,
        limit=3,
        query_filter=Filter(
            must=[FieldCondition(key="topic", match=MatchValue(value="animals"))]
        ),
    )
    for point in results.points:
        print(f"  score={point.score:.4f}  {point.payload['document']}")


if __name__ == "__main__":
    main()
