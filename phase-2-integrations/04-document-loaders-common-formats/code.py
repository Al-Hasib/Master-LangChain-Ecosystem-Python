"""
Phase 2 - Topic 04: Document Loaders - Common Formats

Loads the same conceptual content from PDF, CSV, Markdown, JSON, and SQL into the
SAME shape: list[Document]. A web-page load is included and skipped gracefully if
there's no network access.

Run:
    python code.py
"""

import csv
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def show(label: str, documents) -> None:
    print(f"\n[{label}] {len(documents)} Document(s)")
    if documents:
        first = documents[0]
        preview = first.page_content[:80].replace("\n", " ")
        print(f"  example: page_content={preview!r} metadata={first.metadata}")


def load_pdf(tmp_dir: Path):
    from langchain_community.document_loaders import PyPDFLoader
    from pypdf import PdfWriter

    pdf_path = tmp_dir / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    # Blank pages have no extractable text - this demonstrates the LOADER mechanics
    # (one Document per page, metadata populated) rather than text extraction quality.
    return PyPDFLoader(str(pdf_path)).load()


def load_csv(tmp_dir: Path):
    from langchain_community.document_loaders import CSVLoader

    csv_path = tmp_dir / "policies.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["policy", "description"])
        writer.writerow(["returns", "Returns accepted within 30 days of purchase."])
        writer.writerow(["shipping", "Free shipping for premium plan subscribers."])

    return CSVLoader(file_path=str(csv_path)).load()


def load_markdown(tmp_dir: Path):
    from langchain_community.document_loaders import TextLoader

    md_path = tmp_dir / "handbook.md"
    md_path.write_text(
        "# Support Hours\n\nOur support team is available 9am-6pm, Monday-Friday.\n",
        encoding="utf-8",
    )
    # TextLoader keeps the dependency list light; UnstructuredMarkdownLoader is the
    # structure-aware (headers, lists) alternative if you need that - see doc.md.
    return TextLoader(str(md_path), encoding="utf-8").load()


def load_json_manually():
    """No dedicated loader used here - JSONLoader needs the native `jq` library,
    which is painful to install on Windows. Mapping records to Documents by hand is
    just as correct and avoids that dependency headache."""
    from langchain_core.documents import Document

    records = json.loads(
        '[{"faq": "How do I reset my password?", '
        '"answer": "Use the \'forgot password\' link on the login page."}]'
    )
    return [
        Document(page_content=record["answer"], metadata={"source": "faq.json", "question": record["faq"]})
        for record in records
    ]


def load_sql_manually():
    """Same manual pattern as JSON: one Document per row, columns become metadata."""
    from langchain_core.documents import Document

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE articles (id INTEGER, title TEXT, body TEXT)")
    conn.execute(
        "INSERT INTO articles VALUES (1, 'Refunds', 'Refunds are processed within 5 business days.')"
    )
    rows = conn.execute("SELECT id, title, body FROM articles").fetchall()
    conn.close()

    return [
        Document(page_content=body, metadata={"source": "articles_table", "id": id_, "title": title})
        for id_, title, body in rows
    ]


def load_web_page():
    try:
        from langchain_community.document_loaders import WebBaseLoader

        return WebBaseLoader("https://docs.langchain.com/oss/python/langchain/overview").load()
    except Exception as exc:  # noqa: BLE001 - network can fail in many ways
        print(f"\n[web] skipped (no network access or fetch failed): {exc}")
        return None


def main() -> None:
    try:
        import langchain_community  # noqa: F401
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        show("pdf", load_pdf(tmp_dir))
        show("csv", load_csv(tmp_dir))
        show("markdown", load_markdown(tmp_dir))
        show("json (manual)", load_json_manually())
        show("sql (manual)", load_sql_manually())

    web_documents = load_web_page()
    if web_documents is not None:
        show("web", web_documents)


if __name__ == "__main__":
    main()
