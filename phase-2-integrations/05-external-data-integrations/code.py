"""
Phase 2 - Topic 05: External Data Integrations

Builds a small "external API -> Document" adapter against the public GitHub REST API
(no auth token required for public data). The same pattern applies to Notion, Slack,
Google Drive, or any system with no dedicated LangChain loader - fetch, then map each
record into a Document with meaningful metadata.

Run:
    python code.py
"""

import json
import sys
import urllib.error
import urllib.request


def fetch_github_readme_as_document(owner: str, repo: str):
    """Adapter: GitHub API response -> Document. Swap this function's body for
    Notion's SDK / Slack's SDK / Google Drive's SDK and the shape stays the same."""
    from langchain_core.documents import Document

    api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    request = urllib.request.Request(
        api_url, headers={"Accept": "application/vnd.github.raw+json"}
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        content = response.read().decode("utf-8")

    return Document(
        page_content=content,
        metadata={
            "source": "github",
            "repo": f"{owner}/{repo}",
            "url": f"https://github.com/{owner}/{repo}",
        },
    )


def fetch_github_issues_as_documents(owner: str, repo: str, limit: int = 3):
    """Same adapter pattern applied to a second endpoint - proves the pattern
    generalizes, which is the actual point of this topic."""
    from langchain_core.documents import Document

    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues?per_page={limit}"
    request = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
        issues = json.loads(response.read().decode("utf-8"))

    return [
        Document(
            page_content=issue.get("body") or "(no description)",
            metadata={
                "source": "github",
                "repo": f"{owner}/{repo}",
                "issue_number": issue["number"],
                "title": issue["title"],
                "url": issue["html_url"],
            },
        )
        for issue in issues
        if "pull_request" not in issue  # skip PRs, the issues endpoint includes both
    ]


def main() -> None:
    try:
        import langchain_core  # noqa: F401
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    owner, repo = "langchain-ai", "langchain"
    try:
        readme_doc = fetch_github_readme_as_document(owner, repo)
        print(f"[github readme] {len(readme_doc.page_content)} chars")
        print(f"  metadata: {readme_doc.metadata}")

        issue_docs = fetch_github_issues_as_documents(owner, repo)
        print(f"\n[github issues] {len(issue_docs)} Document(s)")
        for doc in issue_docs:
            print(f"  - {doc.metadata['title']} ({doc.metadata['url']})")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"[skipped] couldn't reach the GitHub API (no network access?): {exc}")


if __name__ == "__main__":
    main()
