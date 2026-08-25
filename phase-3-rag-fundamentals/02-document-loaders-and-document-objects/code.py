"""
Phase 3 - Topic 02: Document Loaders & Document Objects

Loads a generated PDF and a generated CSV (same tempfile trick as Phase 2 Topic 04)
and prints their Documents' page_content/metadata to show every loader produces the
same shape - the shape everything downstream in Phase 3 operates on.

Run:
    python code.py
"""

import csv
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def show(label: str, documents) -> None:
    print(f"\n[{label}] {len(documents)} Document(s)")
    for doc in documents:
        preview = doc.page_content[:80].replace("\n", " ")
        print(f"  page_content={preview!r}")
        print(f"  metadata={doc.metadata}")


def load_pdf(tmp_dir: Path):
    from langchain_community.document_loaders import PyPDFLoader
    from pypdf import PdfWriter

    pdf_path = tmp_dir / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    # Blank pages -> empty page_content. This demonstrates the LOADER mechanics (one
    # Document per page, metadata["page"] auto-populated) - Topic 07 uses a PDF with
    # real text once extraction quality actually matters.
    return PyPDFLoader(str(pdf_path)).load()


def load_csv(tmp_dir: Path):
    from langchain_community.document_loaders import CSVLoader

    csv_path = tmp_dir / "faq.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "answer"])
        writer.writerow(["What's your return window?", "30 days with a valid receipt."])
        writer.writerow(["Do you offer free shipping?", "Yes, on orders over $50 for premium members."])

    # CSVLoader gives one Document per row - real, non-empty page_content this time.
    return CSVLoader(file_path=str(csv_path)).load()


def build_document_by_hand():
    """A loader isn't magic - it's exactly this constructor call, automated."""
    from langchain_core.documents import Document

    return Document(
        page_content="Gift cards do not expire and can be used online or in-store.",
        metadata={"source": "handbook.md", "section": "payments"},
    )


def main() -> None:
    try:
        import langchain_community  # noqa: F401
        import pypdf  # noqa: F401
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        show("pdf (loader)", load_pdf(tmp_dir))
        show("csv (loader)", load_csv(tmp_dir))

    show("hand-built", [build_document_by_hand()])

    print(
        "\nAll three came from completely different sources (PDF file, CSV file, "
        "plain Python) but share the exact same page_content/metadata shape."
    )


if __name__ == "__main__":
    main()
