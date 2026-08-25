# Phase 2 — LangChain Integrations

**Status:** ✅ Fully built — every topic has `doc.md` and `code.py`.

**Teaching point for this whole phase:** don't teach integrations as isolated APIs —
teach the abstraction (`init_chat_model`, `Document`, `VectorStore`, `Retriever`) once,
then show how different providers implement it.

## Topics

01. [Model Integration Pattern](01-model-integration-pattern/doc.md) — one interface (`init_chat_model` / `BaseChatModel`), many providers; how swapping providers changes zero application code.
02. [Provider Walkthrough: OpenAI, Anthropic, Gemini](02-provider-walkthrough-openai-anthropic-gemini/doc.md) — auth, model params, cost/latency tradeoffs across the three.
03. [Local & Alternative Providers](03-local-and-alternative-providers/doc.md) — Ollama (local, private, free) and OpenRouter (provider-agnostic routing).
04. [Document Loaders — Common Formats](04-document-loaders-common-formats/doc.md) — PDF, web pages, CSV, JSON, Markdown, SQL database rows as `Document` objects.
05. [External Data Integrations](05-external-data-integrations/doc.md) — Google Drive, Notion, GitHub, Slack/generic REST APIs as data sources.
06. [Vector Store Integration Pattern](06-vector-store-integration-pattern/doc.md) — Chroma, FAISS, Qdrant, Pinecone, pgvector behind the same `VectorStore` interface.
07. [Choosing a Vector Database](07-choosing-a-vector-database/doc.md) — local vs managed, cost, filtering, scale, hybrid-search support — decision framework.
08. [Mini Project: Multi-Source Connector](08-mini-project-multi-source-connector/doc.md) — one ingestion pipeline that normalizes CSV + Markdown + GitHub API into the same `Document` schema and loads it into Chroma.

## Running the examples

```bash
pip install -r ../requirements.txt
cp ../.env.example ../.env   # fill in OPENAI_API_KEY at minimum
python 01-model-integration-pattern/code.py
```

## Phase project

**Multi-Source Connector** — a single ingestion script that pulls from 2–3 heterogeneous
sources, normalizes to `Document`s with consistent metadata, and writes to a vector
store chosen using the Phase 2 decision framework.
