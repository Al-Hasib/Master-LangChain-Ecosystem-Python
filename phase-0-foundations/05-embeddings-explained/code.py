"""
Phase 0 - Topic 05: Embeddings Explained

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
QUERY = "an animal making sounds outside"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp .env.example .env\n2) fill in your key\n3) re-run"
        )
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    client = OpenAI(api_key=api_key)
    model = "text-embedding-3-small"

    all_texts = SENTENCES + [QUERY]
    response = client.embeddings.create(model=model, input=all_texts)
    vectors = [item.embedding for item in response.data]

    *sentence_vectors, query_vector = vectors

    print(f"Query: {QUERY!r}")
    print(f"Embedding dimension: {len(query_vector)}\n")

    scored = [
        (sentence, cosine_similarity(query_vector, vec))
        for sentence, vec in zip(SENTENCES, sentence_vectors)
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    print("Ranked by semantic similarity to the query:")
    for sentence, score in scored:
        print(f"  {score:.4f}  {sentence}")


if __name__ == "__main__":
    main()
