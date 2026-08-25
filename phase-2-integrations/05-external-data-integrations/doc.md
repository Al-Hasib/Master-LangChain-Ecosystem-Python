# 05 — External Data Integrations

## Problem

Topic 04's sources were local files. Most real knowledge lives in third-party systems —
Google Drive, Notion, GitHub, Slack — reachable only through their APIs, usually behind
auth. The interface should stay the same as Topic 04 even though *getting* the data is
now much more involved.

## Concept

LangChain ships loaders for many external systems (`GoogleDriveLoader`, `NotionDBLoader`,
`GitHubIssuesLoader`, `SlackDirectoryLoader`, and more in `langchain_community` /
dedicated integration packages) — each still returns `list[Document]`, same as Topic 04.
What's different is what's needed *before* `.load()` can be called:

| Source | Auth needed | What one `Document` typically maps to |
|---|---|---|
| Google Drive | OAuth credentials / service account | one file (Doc, Sheet exported as text) |
| Notion | integration token + database/page ID | one page or database row |
| GitHub | personal access token (for private repos) | one issue, PR, or file |
| Slack | bot token + export/API access | one message or thread |
| Generic REST API | API key / OAuth (varies) | one API response mapped to a `Document`, same manual pattern as Topic 04's JSON/SQL |

**The general pattern for "a system with no dedicated loader"** — which is common —
is exactly Topic 04's manual JSON/SQL pattern: call the API, get structured data back,
map each record to a `Document` with meaningful `metadata` (source system, IDs, URLs
back to the original).

```text
External API (auth) -> raw JSON/response -> map each record -> Document(page_content, metadata)
```

## Minimal code

`code.py` builds a small "external API to Document" adapter against the public GitHub
REST API (no auth token required for public repo data, so it runs for every viewer) —
fetching a repo's README and mapping it into a `Document` with `source`/`url` metadata,
demonstrating the exact pattern you'd apply to Notion/Slack/Drive with their SDKs
swapped in.

## Production notes

Store external-source credentials the same way as model API keys (env vars, never
committed — Phase 10 covers proper secrets management). Cache/re-fetch on a schedule
rather than hitting external APIs on every request; most of these have rate limits.

## Debugging

- `401`/`403` errors → token missing required scopes (e.g. a GitHub token without
  `repo` scope can't read private repository content).
- Loader returns fewer documents than expected → check pagination — many APIs cap
  results per page and need the loader (or your manual adapter) to page through results.

## Mini challenge

Extend `code.py`'s GitHub adapter to also fetch and map the repo's open issues (one
`Document` per issue) using the same `metadata`-mapping pattern.
