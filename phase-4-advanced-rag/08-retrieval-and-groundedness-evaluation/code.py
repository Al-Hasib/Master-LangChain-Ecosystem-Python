"""
Phase 4 - Topic 08: Retrieval & Groundedness Evaluation

Generates two answers from the SAME retrieved context - one prompted to stick
strictly to it, one prompted loosely (inviting elaboration) - and runs an
LLM-as-judge groundedness check against both.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

NIMBUS_DOCS = [
    "The Apollo plan is Nimbus's enterprise tier: a dedicated account manager, "
    "a 600 requests/minute API limit, and priority onboarding.",
    "Support response times: Standard plan gets email support within 2 business days. "
    "Apollo plan gets a 1-hour SLA via a dedicated Slack channel.",
]

QUERY = "What support does the Apollo plan include?"


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
        from pydantic import BaseModel, Field
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    documents = [Document(page_content=text) for text in NIMBUS_DOCS]
    context = "\n\n".join(doc.page_content for doc in documents)
    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)

    # --- Answer 1: strictly grounded prompt ---
    strict_answer = model.invoke(
        f"Answer using ONLY the context below. Do not add any detail not present in it.\n\n"
        f"Context:\n{context}\n\nQuestion: {QUERY}"
    ).content

    # --- Answer 2: loose prompt that invites elaboration beyond the context ---
    loose_answer = model.invoke(
        f"Context:\n{context}\n\nQuestion: {QUERY}\n\n"
        "Be thorough and helpful - give the user a complete, confident answer covering "
        "everything they'd likely want to know about Apollo plan support, including "
        "typical response channels and what's generally included at that tier."
    ).content

    class GroundednessCheck(BaseModel):
        grounded: bool = Field(description="True only if EVERY claim is supported by the context")
        unsupported_claims: list[str] = Field(
            description="Claims present in the answer but NOT found in the context (empty if grounded)"
        )
        reasoning: str = Field(description="One or two sentence explanation")

    judge = model.with_structured_output(GroundednessCheck)

    def check(label: str, answer: str) -> None:
        result = judge.invoke(
            f"Context:\n{context}\n\nAnswer:\n{answer}\n\n"
            "Is every claim in the answer directly supported by the context? "
            "Paraphrasing is fine; adding new specifics that aren't in the context is not."
        )
        print(f"--- {label} ---")
        print(f"Answer: {answer}\n")
        print(f"Grounded: {result.grounded}")
        if result.unsupported_claims:
            print(f"Unsupported claims: {result.unsupported_claims}")
        print(f"Reasoning: {result.reasoning}\n")

    print(f"Query: {QUERY}\n")
    check("Strict prompt (context-only)", strict_answer)
    check("Loose prompt (invites elaboration)", loose_answer)


if __name__ == "__main__":
    main()
