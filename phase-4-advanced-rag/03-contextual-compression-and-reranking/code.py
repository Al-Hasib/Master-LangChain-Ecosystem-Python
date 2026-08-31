"""
Phase 4 - Topic 03: Contextual Compression & Reranking

Retrieves a wide candidate set, then (a) compresses each candidate down to only the
query-relevant span, and (b) reranks the same candidates with an LLM-as-reranker
(structured relevance score) instead of relying on raw embedding-distance order.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Nimbus docs, each padded with a sentence or two NOT relevant to the demo query -
# mimicking real chunks that mix one useful sentence with surrounding filler.
NIMBUS_DOCS = [
    "Nimbus's onboarding checklist for new engineers includes VPN setup and repo "
    "access requests. Apollo plan customers get a 1-hour support SLA via a dedicated "
    "Slack channel, separate from the standard 2-business-day email queue.",
    "The Nimbus mobile app supports offline mode for documents synced within the last "
    "7 days. Offline sync does not apply to the web dashboard.",
    "Apollo plan API limits are 600 requests/minute, versus 60 requests/minute on "
    "Standard. Rate limit headers are returned on every response as X-RateLimit-Remaining.",
    "Password resets are self-service via the login page's 'Forgot password' link. "
    "Apollo plan admins can also force a reset for any team member from the admin console.",
    "Nimbus's changelog is published monthly. Apollo plan customers additionally get a "
    "private pre-release changelog two weeks before general availability.",
]

QUERY = "What extra support or admin capabilities does the Apollo plan include?"


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def main() -> None:
    require_openai_key()
    try:
        from langchain.chat_models import init_chat_model
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
        from langchain_qdrant import QdrantVectorStore
        from pydantic import BaseModel, Field
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    try:
        # ContextualCompressionRetriever + LLMChainExtractor moved to the separate
        # `langchain-classic` package in the langchain v1 reorganization.
        # pip install langchain-classic  (not yet in requirements.txt - see doc.md)
        from langchain_classic.retrievers import ContextualCompressionRetriever
        from langchain_classic.retrievers.document_compressors import LLMChainExtractor
    except ImportError:
        sys.exit(
            "Missing dependency. Run: pip install -r ../../requirements.txt langchain-classic"
        )

    documents = [Document(page_content=text, metadata={"id": i}) for i, text in enumerate(NIMBUS_DOCS)]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = QdrantVectorStore.from_documents(
        documents, embedding=embeddings, location=":memory:", collection_name="phase4_compression_reranking"
    )
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    print(f"Query: {QUERY}\n")

    # --- Wide candidate retrieval (this is the "retrieve wide" half of the pattern) ---
    k = 5
    candidates = vectorstore.similarity_search(QUERY, k=k)
    print(f"--- Raw candidates (similarity order, k={k}) ---")
    for doc in candidates:
        print(f"  [doc {doc.metadata['id']}] {doc.page_content}")

    # --- (a) Contextual compression: trim each candidate to its relevant span ---
    compressor = LLMChainExtractor.from_llm(model)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=vectorstore.as_retriever(search_kwargs={"k": k})
    )
    compressed = compression_retriever.invoke(QUERY)
    print("\n--- After contextual compression (trimmed to relevant spans) ---")
    for doc in compressed:
        print(f"  [doc {doc.metadata.get('id', '?')}] {doc.page_content!r}")

    # --- (b) LLM-as-reranker: structured relevance score, re-sort by it ---
    # NOTE: this hand-rolled scorer is the example's stand-in for a real reranker
    # (Cohere Rerank / a cross-encoder model) - see doc.md "Production notes".
    class RelevanceScore(BaseModel):
        score: int = Field(description="Relevance of the document to the query, 0-10")
        reason: str = Field(description="One short sentence justifying the score")

    scorer = model.with_structured_output(RelevanceScore)
    scored = []
    for doc in candidates:
        result = scorer.invoke(
            f"Query: {QUERY}\n\nDocument: {doc.page_content}\n\n"
            "Score how relevant this document is to answering the query."
        )
        scored.append((result.score, doc, result.reason))

    scored.sort(key=lambda item: item[0], reverse=True)
    print("\n--- After LLM-as-reranker (re-scored, descending) ---")
    for score, doc, reason in scored:
        print(f"  [doc {doc.metadata['id']}] score={score:2d}  {reason}")


if __name__ == "__main__":
    main()
