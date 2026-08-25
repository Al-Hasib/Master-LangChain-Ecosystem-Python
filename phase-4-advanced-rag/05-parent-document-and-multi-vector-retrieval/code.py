"""
Phase 4 - Topic 05: Parent-Document & Multi-Vector Retrieval

Indexes a long Nimbus runbook with ParentDocumentRetriever: small child chunks get
searched, but the full parent chunk is what's returned for generation - showing the
gap between what matched and what comes back.

Run:
    python code.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# One long document - a Nimbus deployment runbook - split into sections that would
# each make a poor standalone chunk (context lives in the surrounding paragraph).
RUNBOOK = """
Nimbus Deployment Runbook

Section 1: Pre-deploy checks.
Before deploying, confirm the staging environment has passed its smoke tests and that
the on-call engineer has acknowledged the deploy window in the #deploys Slack channel.
Deploys outside business hours require a second engineer's sign-off.

Section 2: Database migrations.
Migrations run automatically via the Atlas migration tool as part of the deploy
pipeline. If a migration fails, the pipeline halts BEFORE the new application version is
promoted - the old version keeps serving traffic. Check the Atlas dashboard for the
failure reason; most failures are lock timeouts caused by a long-running query on the
same table. Re-running the migration after the conflicting query finishes usually
resolves it without a rollback.

Section 3: Rollback procedure.
To roll back, redeploy the previous image tag from the Releases page - this does NOT
automatically revert database migrations, so a rollback after a migration has already
run requires manually running the corresponding down-migration first.

Section 4: Post-deploy verification.
After a deploy completes, check the /healthz endpoint and the error-rate dashboard for
5 minutes before closing the deploy window. A spike above 2% error rate should trigger
an immediate rollback per Section 3.
""".strip()

QUERY = "What should I check after a migration fails during deploy?"


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def main() -> None:
    require_openai_key()
    try:
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    try:
        # ParentDocumentRetriever + InMemoryStore moved to langchain-classic in the
        # langchain v1 reorganization. pip install langchain-classic
        # (not yet in requirements.txt - see doc.md)
        from langchain_classic.retrievers import ParentDocumentRetriever
        from langchain_classic.storage import InMemoryStore
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt langchain-classic")

    documents = [Document(page_content=RUNBOOK, metadata={"source": "deploy-runbook"})]

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(embedding_function=embeddings, collection_name="parent_doc_demo")

    # Small child chunks get embedded and searched; larger parent chunks (one per
    # "Section") are what actually get returned once a child match is found.
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=120, chunk_overlap=0)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=0)

    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=InMemoryStore(),
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )
    retriever.add_documents(documents)

    print(f"Query: {QUERY}\n")

    # What actually matched at the CHILD (small-chunk) level:
    child_matches = vectorstore.similarity_search(QUERY, k=1)
    print("--- Matched CHILD chunk (what was searched) ---")
    print(f"  {child_matches[0].page_content!r}\n")

    # What the retriever actually returns - the full PARENT chunk that child belongs to:
    parent_results = retriever.invoke(QUERY)
    print("--- Returned PARENT chunk (what generation actually sees) ---")
    for doc in parent_results:
        print(f"  {doc.page_content!r}")

    print(
        "\nThe child match alone ('migration failed... check the Atlas dashboard') "
        "doesn't say WHERE that fits in the runbook or what to do next. The parent "
        "chunk includes the full Section 2 paragraph - the actual fix - because "
        "generation reads the parent, not the child that was searched."
    )


if __name__ == "__main__":
    main()
