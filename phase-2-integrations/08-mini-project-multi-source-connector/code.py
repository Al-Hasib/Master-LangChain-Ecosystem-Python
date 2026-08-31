"""
Phase 2 - Topic 08 (Mini Project): Multi-Source Connector

CSV + Markdown + GitHub API -> normalized metadata schema -> one Qdrant collection.

Run:
    python code.py
"""

import csv
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# The shared metadata schema every source gets normalized into.
#   source_type: a category you can filter on later (e.g. "policy", "handbook", "code")
#   source_name: a human-readable identifier for where it came from
#   origin:      "local" or "external"


def load_policies_csv(tmp_dir: Path):
    from langchain_community.document_loaders import CSVLoader

    csv_path = tmp_dir / "policies.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["policy", "description"])
        writer.writerow(["returns", "Returns are accepted within 30 days of purchase."])
        writer.writerow(["shipping", "Premium plan subscribers get free shipping."])

    documents = CSVLoader(file_path=str(csv_path)).load()
    for doc in documents:
        doc.metadata = {"source_type": "policy", "source_name": "policies.csv", "origin": "local"}
    return documents


def load_handbook_markdown(tmp_dir: Path):
    from langchain_community.document_loaders import TextLoader

    md_path = tmp_dir / "handbook.md"
    md_path.write_text(
        "# Support\n\nSupport hours are 9am-6pm, Monday through Friday. "
        "Refunds are processed within 5 business days.\n",
        encoding="utf-8",
    )
    documents = TextLoader(str(md_path), encoding="utf-8").load()
    for doc in documents:
        doc.metadata = {"source_type": "handbook", "source_name": "handbook.md", "origin": "local"}
    return documents


def load_github_readme(owner: str, repo: str):
    from langchain_core.documents import Document

    api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    request = urllib.request.Request(
        api_url, headers={"Accept": "application/vnd.github.raw+json"}
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        content = response.read().decode("utf-8")

    return [
        Document(
            page_content=content[:2000],  # keep it small for this demo
            metadata={"source_type": "code_docs", "source_name": f"{owner}/{repo}", "origin": "external"},
        )
    ]


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )
    try:
        from langchain_openai import OpenAIEmbeddings
        from langchain_qdrant import QdrantVectorStore
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    all_documents = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        all_documents += load_policies_csv(tmp_dir)
        all_documents += load_handbook_markdown(tmp_dir)

    try:
        all_documents += load_github_readme("langchain-ai", "langchain")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"[skipped] github source (no network access?): {exc}")

    print(f"Ingesting {len(all_documents)} documents from {len({d.metadata['source_name'] for d in all_documents})} sources:")
    for doc in all_documents:
        print(f"  - {doc.metadata['source_type']:12s} {doc.metadata['source_name']}")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    store = QdrantVectorStore.from_documents(
        all_documents,
        embedding=embeddings,
        location=":memory:",
        collection_name="phase2_multi_source_connector",
    )

    query = "How does refund and support handling work?"
    print(f"\nQuery: {query!r}")
    for doc in store.similarity_search(query, k=2):
        print(f"  [{doc.metadata['source_type']}/{doc.metadata['source_name']}] "
              f"{doc.page_content[:100].strip()!r}")


if __name__ == "__main__":
    main()
