"""
Capstone 01: Enterprise Knowledge Assistant (Production RAG)

Run:
    python code.py

Demonstrates: chunking + embeddings + retrieval (Phase 3) over an in-code, multi-source
corpus, a relevance-grading pass before generation (Phase 4 Topic 07, single-pass
version), source-cited answers (metadata-driven, not model-claimed), and a running
conversation-memory list across a few sequential questions in one run.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    sys.exit(
        "Missing OPENAI_API_KEY.\n1) cp ../.env.example ../.env\n"
        "2) fill in your key\n3) re-run"
    )

try:
    from langchain.chat_models import init_chat_model
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from pydantic import BaseModel, Field
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r ../requirements.txt")


# ---------------------------------------------------------------------------
# In-code corpus: normalized metadata schema reused from Phase 2 Topic 08
# (source_type / source_name / origin) so a filtered search could later ask
# "only search source_type='policy'" without touching ingestion again.
# ---------------------------------------------------------------------------
RAW_DOCUMENTS = [
    ("policy", "pto-policy.md", "Employees accrue 1.5 days of paid time off per month "
     "worked, capped at 24 days per calendar year. Unused PTO up to 5 days carries over "
     "into the next year; anything beyond that is forfeited on December 31st."),
    ("policy", "remote-work-policy.md", "Employees may work remotely up to 3 days per "
     "week without manager approval. Fully remote arrangements require director "
     "sign-off and a documented home-office safety checklist."),
    ("policy", "expense-policy.md", "Business expenses under $75 do not require "
     "pre-approval but must be submitted with a receipt within 30 days. Expenses over "
     "$75 require manager approval before the purchase is made."),
    ("policy", "security-policy.md", "All laptops must have disk encryption and a "
     "password manager installed before connecting to internal systems. Multi-factor "
     "authentication is mandatory for every internal application."),
    ("policy", "parental-leave-policy.md", "Primary caregivers receive 16 weeks of paid "
     "parental leave; secondary caregivers receive 6 weeks. Leave must be taken within "
     "12 months of the birth or adoption date."),
    ("handbook", "onboarding-handbook.md", "New hires get a laptop, a buddy assigned "
     "for their first 30 days, and a 90-day check-in with their manager. IT provisioning "
     "typically completes before the employee's start date."),
    ("handbook", "engineering-handbook.md", "Engineers deploy to production via pull "
     "request; every PR requires one approving review and a passing CI run before merge. "
     "On-call rotations are weekly and cover business-hours incidents only."),
    ("handbook", "performance-review-handbook.md", "Performance reviews happen twice a "
     "year, in June and December. Each review combines a self-assessment, manager "
     "feedback, and two peer reviews chosen by the employee."),
    ("handbook", "benefits-handbook.md", "Health insurance coverage begins on an "
     "employee's first day of employment, with no waiting period. The company matches "
     "401(k) contributions up to 4% of base salary."),
    ("handbook", "travel-handbook.md", "Domestic flights should be booked at least 14 "
     "days in advance through the corporate travel portal. Employees may keep loyalty "
     "program points earned on business travel."),
    ("handbook", "equipment-handbook.md", "Standard equipment includes a laptop and one "
     "external monitor; a second monitor or specialized hardware requires manager "
     "approval via the equipment request form."),
    ("policy", "data-retention-policy.md", "Customer support tickets are retained for 3 "
     "years after resolution. Internal chat logs are retained for 1 year unless placed "
     "under legal hold."),
]


class RelevanceGrade(BaseModel):
    """Structured grade for whether one retrieved chunk actually supports the question."""

    is_relevant: bool = Field(
        description="True only if this chunk contains information that directly "
        "helps answer the question."
    )
    reason: str = Field(description="One short sentence explaining the grade.")


def build_corpus() -> list[Document]:
    return [
        Document(
            page_content=text,
            metadata={"source_type": source_type, "source_name": name, "origin": "local"},
        )
        for source_type, name, text in RAW_DOCUMENTS
    ]


def build_vector_store(documents: list[Document]) -> Chroma:
    # Phase 3 Topic 03: chunk before embedding. These docs are short (1-2 sentences)
    # so most become a single chunk each - the splitter still matters once real
    # multi-paragraph policy PDFs replace this in-code corpus.
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
    chunks = splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    # Ephemeral in-memory client - see doc.md "What's simplified".
    return Chroma.from_documents(chunks, embedding=embeddings)


def grade_chunks(model, question: str, chunks: list[Document]) -> list[Document]:
    """Phase 4 Topic 07, single-pass version: drop any retrieved chunk that an LLM
    grader says doesn't actually ground an answer to this question, instead of
    trusting top-k similarity blindly."""
    grader = model.with_structured_output(RelevanceGrade)
    kept = []
    for chunk in chunks:
        grade = grader.invoke(
            f"Question: {question}\n\nRetrieved chunk:\n{chunk.page_content}\n\n"
            "Does this chunk contain information that directly helps answer the "
            "question?"
        )
        tag = "KEEP" if grade.is_relevant else "DROP"
        print(f"    [grade:{tag}] {chunk.metadata['source_name']} - {grade.reason}")
        if grade.is_relevant:
            kept.append(chunk)
    return kept


def answer_question(model, store: Chroma, question: str, history: list[str]) -> str:
    retriever = store.as_retriever(search_kwargs={"k": 4})
    retrieved = retriever.invoke(question)
    print(f"  Retrieved {len(retrieved)} chunk(s), grading for relevance:")
    grounded = grade_chunks(model, question, retrieved)

    if not grounded:
        answer = (
            "I don't have grounded information in the knowledge base to answer "
            "that confidently."
        )
        history.append(f"Q: {question}\nA: {answer}")
        return answer

    # Citations are built from real metadata, not asked of the model - the same
    # "ground truth over model claim" idea as Phase 0 Topic 08's mini project.
    context = "\n\n".join(
        f"[{doc.metadata['source_name']}] {doc.page_content}" for doc in grounded
    )
    conversation_so_far = "\n\n".join(history[-3:])  # short rolling memory window

    prompt = (
        "You are an internal company knowledge assistant. Answer the question using "
        "ONLY the provided context. Cite the source file for every claim using "
        "[source_name] notation. If the context doesn't fully answer the question, "
        "say what's missing.\n\n"
        f"Prior conversation (for context, may be empty):\n{conversation_so_far}\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    response = model.invoke(prompt)
    answer = response.content
    history.append(f"Q: {question}\nA: {answer}")
    return answer


def main() -> None:
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    print("Building corpus and vector store...")
    documents = build_corpus()
    store = build_vector_store(documents)
    print(f"Indexed {len(documents)} source documents.\n")

    # Sequential questions in one run - the second and third deliberately depend on
    # the earlier turns to prove conversation memory is actually being used.
    questions = [
        "How much PTO do employees accrue, and does it carry over?",
        "If I used only half my carryover allowance last year, how many days would "
        "I have lost?",
        "What's the company's policy on quantum computing research budgets?",
    ]

    history: list[str] = []
    for question in questions:
        print(f"=== Question: {question} ===")
        answer = answer_question(model, store, question, history)
        print(f"  Answer: {answer}\n")


if __name__ == "__main__":
    main()
