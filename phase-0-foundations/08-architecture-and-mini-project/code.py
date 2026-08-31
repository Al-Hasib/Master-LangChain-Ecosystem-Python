"""
Phase 0 - Topic 08: Architecture of a Modern AI App & Mini Project

A tiny CLI-style app with NO framework: chat model + one tool + a vector-backed
knowledge base + structured JSON output. Everything Phase 1's `create_agent` will
replace, written out by hand so the abstraction lands as a real simplification.

Run:
    python code.py
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE_BASE = [
    "The company's return policy allows returns within 30 days of purchase.",
    "Support hours are 9am-6pm, Monday through Friday.",
    "Premium plan subscribers get free shipping on all orders.",
]

ANSWER_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "answer",
        "schema": {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "source": {
                    "type": "string",
                    "enum": ["knowledge_base", "general_knowledge"],
                },
            },
            "required": ["answer", "source"],
            "additionalProperties": False,
        },
    },
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search internal company policy docs. Only use for "
            "questions about this company's policies.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }
]


COLLECTION_NAME = "phase0_mini_project"
EMBEDDING_MODEL = "text-embedding-3-small"


def embed(openai_client, texts: list[str]) -> list[list[float]]:
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def build_collection(qdrant_client, openai_client):
    from qdrant_client.models import Distance, PointStruct, VectorParams

    vectors = embed(openai_client, KNOWLEDGE_BASE)
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
    )
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(id=i, vector=vector, payload={"document": doc})
            for i, (vector, doc) in enumerate(zip(vectors, KNOWLEDGE_BASE))
        ],
    )
    return qdrant_client


def answer_question(openai_client, collection, question: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": "Answer the user's question. Use the search tool only for "
            "questions about this company's policies.",
        },
        {"role": "user", "content": question},
    ]

    # Step 1: let the model decide whether to search.
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, tools=TOOLS
    )
    message = response.choices[0].message

    source = "general_knowledge"
    if message.tool_calls:
        call = message.tool_calls[0]
        query = json.loads(call.function.arguments)["query"]
        query_vector = embed(openai_client, [query])[0]
        results = collection.query_points(
            collection_name=COLLECTION_NAME, query=query_vector, limit=2
        )
        context = "\n".join(point.payload["document"] for point in results.points)

        messages.append(message)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": context})
        source = "knowledge_base"

    # Step 2: final answer, forced into a strict JSON schema.
    final = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, response_format=ANSWER_SCHEMA
    )
    result = json.loads(final.choices[0].message.content)
    result["source"] = source  # ground-truth source, not just what the model claims
    return result


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp .env.example .env\n2) fill in your key\n3) re-run"
        )
    try:
        from openai import OpenAI
        from qdrant_client import QdrantClient
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    openai_client = OpenAI(api_key=api_key)
    qdrant_client = QdrantClient(location=":memory:")
    collection = build_collection(qdrant_client, openai_client)

    questions = [
        "What's your return policy?",
        "What is the capital of France?",
    ]
    for question in questions:
        result = answer_question(openai_client, collection, question)
        print(f"\nQ: {question}")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
