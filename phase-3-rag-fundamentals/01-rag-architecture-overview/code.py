"""
Phase 3 - Topic 01: RAG Architecture Overview

Minimal end-to-end 2-step RAG: retrieve (embed + similarity search over a tiny
in-code corpus) then generate (stuff retrieved docs into a prompt, call the LLM).
No loaders yet - Documents are built by hand from a list of strings (Topic 02
introduces real file loaders).

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# A tiny fictional knowledge base - just enough facts to show retrieval actually
# narrowing down to relevant content, not enough to be a realistic corpus (Topic 07
# builds a real multi-page-PDF pipeline).
CORPUS = [
    "Northwind Outfitters accepts returns within 30 days of purchase with a valid receipt.",
    "Refunds are processed within 5-7 business days after the returned item is received.",
    "Premium members get free standard shipping on all orders over $50.",
    "Customer support is available 9am-6pm Eastern Time, Monday through Friday.",
    "The TrailBlazer 40L backpack has a lifetime warranty against manufacturing defects.",
]

PROMPT_TEMPLATE = """Answer the question using ONLY the context below. \
If the context doesn't contain the answer, say "I don't know based on the provided context."

Context:
{context}

Question: {question}"""


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )
    try:
        from langchain.chat_models import init_chat_model
        from langchain_core.documents import Document
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import OpenAIEmbeddings
        from langchain_qdrant import QdrantVectorStore
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    # --- Build Documents by hand (no loader - see Topic 02) ---
    documents = [Document(page_content=text) for text in CORPUS]

    # --- Step 0 (one-time): embed + store, exactly Phase 2 Topic 06's pattern ---
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = QdrantVectorStore.from_documents(
        documents,
        embedding=embeddings,
        location=":memory:",
        collection_name="phase3_topic01_rag_overview",
    )

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | model  # LCEL, Phase 1 Topic 03

    questions = [
        "How long do I have to return something?",  # answerable from the corpus
        "Do you ship internationally?",  # NOT in the corpus at all
    ]

    for question in questions:
        # --- Step 1: RETRIEVE ---
        retrieved = vector_store.similarity_search(question, k=2)
        context = "\n".join(f"- {doc.page_content}" for doc in retrieved)

        # --- Step 2: GENERATE ---
        response = chain.invoke({"context": context, "question": question})

        print(f"Question: {question}")
        print(f"  Retrieved {len(retrieved)} doc(s):")
        for doc in retrieved:
            print(f"    - {doc.page_content}")
        print(f"  Answer: {response.content}\n")


if __name__ == "__main__":
    main()
