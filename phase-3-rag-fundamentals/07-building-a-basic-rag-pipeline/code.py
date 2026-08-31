"""
Phase 3 - Topic 07: Building a Basic RAG Pipeline

Phase project: PDF Knowledge Assistant.
PDF -> Loader -> Splitter -> Embeddings -> Vector DB -> Retriever -> LLM -> Answer + Sources

Generates a small multi-page PDF WITH REAL TEXT (pypdf alone can only write blank
pages - see Topic 02), then runs the full pipeline and prints answers with page
citations pulled from Document metadata, not from the LLM.

Run:
    python code.py
"""

import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Page-by-page content for the generated PDF - each string becomes one PDF page.
PDF_PAGES = [
    "Northwind Outfitters Customer Handbook\n\n"
    "Returns Policy: Northwind Outfitters accepts returns within 30 days of purchase "
    "with a valid receipt. Items must be unworn and in original packaging.",

    "Refunds: Refunds are processed within 5-7 business days after the returned item "
    "is received at our warehouse. Refunds are issued to the original payment method.",

    "Product Warranty: The TrailBlazer 40L backpack has a lifetime warranty against "
    "manufacturing defects, covering broken zippers, torn seams, and buckle failures.",

    "Support: Customer support is available 9am-6pm Eastern Time, Monday through "
    "Friday, by phone, live chat, or email.",
]

PROMPT_TEMPLATE = """Answer the question using ONLY the context below. Each context \
snippet is tagged with the page it came from. If the context doesn't contain the \
answer, say "I don't know based on the provided context."

Context:
{context}

Question: {question}"""


def generate_pdf(tmp_dir: Path) -> Path:
    """Write a real multi-page PDF with actual extractable text. pypdf can only
    write blank pages (Topic 02) - reportlab is the standard tool for drawing text."""
    from reportlab.pdfgen import canvas

    pdf_path = tmp_dir / "handbook.pdf"
    doc = canvas.Canvas(str(pdf_path), pagesize=(400, 300))
    for page_text in PDF_PAGES:
        y = 260
        for line in _wrap_text(page_text, width=70):
            doc.drawString(30, y, line)
            y -= 16
        doc.showPage()  # end this page, start the next
    doc.save()
    return pdf_path


def _wrap_text(text: str, width: int) -> list[str]:
    """Tiny manual word-wrap so drawString lines don't run off the page."""
    words = text.replace("\n", " ").split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def format_context(documents) -> str:
    """Tag each chunk with its source page so both the LLM and our own citation
    logic can trace an answer back to a page - the LLM sees the tag, but we build
    the final citation list ourselves from metadata (see main())."""
    lines = []
    for doc in documents:
        page = doc.metadata.get("page", "?")
        lines.append(f"[page {page}] {doc.page_content}")
    return "\n".join(lines)


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )
    try:
        from langchain.chat_models import init_chat_model
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import OpenAIEmbeddings
        from langchain_qdrant import QdrantVectorStore
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")
    try:
        import reportlab  # noqa: F401
    except ImportError:
        sys.exit(
            "Missing dependency 'reportlab' (used only to generate a sample PDF "
            "with real text - not in requirements.txt). Run: pip install reportlab"
        )

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = generate_pdf(Path(tmp))

        # 1) LOADER (Topic 02 / Phase 2 Topic 04) - one Document per page.
        pages = PyPDFLoader(str(pdf_path)).load()
        print(f"[1/6 loader] {len(pages)} page(s) loaded from {pdf_path.name}")

        # 2) SPLITTER (Topic 03) - split PER-PAGE Documents so page metadata carries
        # onto every chunk. Splitting a pre-concatenated string would lose that.
        splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
        chunks = splitter.split_documents(pages)
        print(f"[2/6 splitter] {len(chunks)} chunk(s), each still tagged with its page")

        # 3) EMBEDDINGS + 4) VECTOR DB (Topic 04)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = QdrantVectorStore.from_documents(
            chunks,
            embedding=embeddings,
            location=":memory:",
            collection_name="phase3_topic07_rag_pipeline",
        )
        print("[3-4/6 embeddings+store] chunks embedded and indexed in Qdrant")

        # 5) RETRIEVER (Topic 05)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        print("[5/6 retriever] ready\n")

        model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        chain = prompt | model  # LCEL, Phase 1 Topic 03

        questions = [
            "What's the warranty on the backpack?",
            "How long do refunds take?",
        ]

        for question in questions:
            retrieved = retriever.invoke(question)
            context = format_context(retrieved)
            response = chain.invoke({"context": context, "question": question})

            # 6) ANSWER + SOURCES - citations built from metadata, never from the LLM.
            pages_cited = sorted({doc.metadata.get("page", "?") for doc in retrieved})

            print(f"Q: {question}")
            print(f"A: {response.content}")
            print(f"   Sources: page(s) {pages_cited} of {pdf_path.name}\n")


if __name__ == "__main__":
    main()
