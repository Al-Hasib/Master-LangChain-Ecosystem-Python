"""
Phase 0 - Topic 07: RAG vs Agent vs Workflow

Same knowledge base, two shapes:
  1) Fixed RAG workflow  - ALWAYS retrieve, then generate.
  2) Agent decision       - model decides whether retrieval is even needed.

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


def build_collection(client, embedding_fn):
    import chromadb  # noqa: F401 (imported for clarity of dependency; client passed in)

    collection = client.create_collection(
        name="phase0_rag_demo", embedding_function=embedding_fn
    )
    collection.add(
        documents=KNOWLEDGE_BASE, ids=[f"kb-{i}" for i in range(len(KNOWLEDGE_BASE))]
    )
    return collection


def fixed_rag_workflow(openai_client, collection, question: str) -> str:
    """Workflow shape: retrieval ALWAYS happens, no matter the question."""
    results = collection.query(query_texts=[question], n_results=2)
    context = "\n".join(results["documents"][0])
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Answer using ONLY the provided context. "
                "If the context doesn't contain the answer, say so.",
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        max_tokens=80,
    )
    return f"[retrieved {len(results['documents'][0])} docs] {response.choices[0].message.content}"


def agent_decision_step(openai_client, collection, question: str) -> str:
    """Agent shape: the model decides whether retrieval is needed at all."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search company policy documents. Only use this for "
                "questions about company policy - not for general knowledge or math.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        }
    ]
    messages = [{"role": "user", "content": question}]
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, tools=tools, max_tokens=80
    )
    message = response.choices[0].message

    if not message.tool_calls:
        return f"[no retrieval] {message.content}"

    call = message.tool_calls[0]
    query = json.loads(call.function.arguments)["query"]
    results = collection.query(query_texts=[query], n_results=2)
    context = "\n".join(results["documents"][0])

    messages.append(message)
    messages.append({"role": "tool", "tool_call_id": call.id, "content": context})
    final = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return f"[retrieved via agent decision] {final.choices[0].message.content}"


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp .env.example .env\n2) fill in your key\n3) re-run"
        )
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        from openai import OpenAI
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    openai_client = OpenAI(api_key=api_key)
    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key, model_name="text-embedding-3-small"
    )
    chroma_client = chromadb.Client()
    collection = build_collection(chroma_client, embedding_fn)

    questions = [
        "What's your return policy?",
        "What's 12 times 7?",  # doesn't need the knowledge base at all
    ]

    for question in questions:
        print(f"\nQuestion: {question}")
        print("  Fixed RAG workflow: " + fixed_rag_workflow(openai_client, collection, question))
        print("  Agent decision:     " + agent_decision_step(openai_client, collection, question))


if __name__ == "__main__":
    main()
