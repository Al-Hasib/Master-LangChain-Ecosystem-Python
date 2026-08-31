"""
Phase 4 - Topic 07: Document Relevance Grading & Self-Correction

Grades retrieved documents relevant/not before generation, filters out the
irrelevant ones, and re-queries ONCE (rewriting the query) if nothing relevant
survives - then generates only from documents that passed grading.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Same Nimbus corpus as Topics 01-02: naive top-k on this query grabs docs that
# LOOK related (mention "refund" or "Apollo") but don't answer eligibility - a good
# test case for a grader to actually catch.
NIMBUS_DOCS = [
    "Nimbus Standard and Pro plans include a 30-day money-back guarantee. "
    "Refund requests are filed through the Billing dashboard.",
    "The Apollo plan is Nimbus's enterprise tier: a dedicated account manager, "
    "a 600 requests/minute API limit, and priority onboarding.",
    "Nimbus API rate limits are 60 requests/minute on Standard plans and "
    "600 requests/minute on Apollo plans.",
    "Annual enterprise contracts signed under Nimbus's Master Services Agreement "
    "are final sale once the account is provisioned; the standard 30-day refund "
    "window does not apply to them. Exceptions require account-manager approval.",
    "Password resets are self-service via the login page's 'Forgot password' link; "
    "the reset link expires after 15 minutes.",
]

QUERY = "I'm on the Apollo plan and want a refund - am I eligible?"
MAX_RETRIES = 1


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

    documents = [Document(page_content=text, metadata={"id": i}) for i, text in enumerate(NIMBUS_DOCS)]
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = QdrantVectorStore.from_documents(
        documents, embedding=embeddings, location=":memory:", collection_name="phase4_relevance_grading"
    )
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    class RelevanceGrade(BaseModel):
        relevant: bool = Field(description="True only if the document directly helps answer the question")
        reason: str = Field(description="One short sentence justifying the grade")

    grader = model.with_structured_output(RelevanceGrade)

    def grade_docs(question: str, docs) -> list:
        """Grade each doc; return only those graded relevant."""
        kept = []
        for doc in docs:
            grade = grader.invoke(
                f"Question: {question}\n\nDocument: {doc.page_content}\n\n"
                "Is this document DIRECTLY relevant to answering the question? "
                "Topically related is not enough - it must actually help answer it."
            )
            mark = "relevant" if grade.relevant else "NOT relevant"
            print(f"    [doc {doc.metadata['id']}] {mark} - {grade.reason}")
            if grade.relevant:
                kept.append(doc)
        return kept

    def rewrite_query(question: str) -> str:
        prompt = (
            "Rewrite this question into a more explicit search query, naming the "
            "entities involved and likely policy terms. Return ONLY the query.\n\n"
            f"Question: {question}"
        )
        return model.invoke(prompt).content.strip()

    print(f"Query: {QUERY}\n")

    query = QUERY
    relevant_docs = []
    for attempt in range(MAX_RETRIES + 1):
        label = "Initial retrieval" if attempt == 0 else f"Retry {attempt} (rewritten query: '{query}')"
        print(f"--- {label} ---")
        candidates = vectorstore.similarity_search(query, k=2)
        for doc in candidates:
            print(f"  retrieved [doc {doc.metadata['id']}] {doc.page_content[:60]}...")
        print("  grading:")
        relevant_docs = grade_docs(QUERY, candidates)  # always grade against the ORIGINAL question

        if relevant_docs:
            break
        if attempt < MAX_RETRIES:
            print("  -> nothing relevant survived grading; rewriting query and retrying once.\n")
            query = rewrite_query(QUERY)

    print()
    if not relevant_docs:
        print("No relevant documents survived after retry - answering honestly rather than guessing.")
        print("Answer: I don't have enough information in the knowledge base to answer that.")
        return

    context = "\n\n".join(doc.page_content for doc in relevant_docs)
    answer = model.invoke(
        f"Answer using ONLY this context:\n{context}\n\nQuestion: {QUERY}"
    ).content
    print(f"Generated from {len(relevant_docs)} graded-relevant doc(s):\n{answer}")


if __name__ == "__main__":
    main()
