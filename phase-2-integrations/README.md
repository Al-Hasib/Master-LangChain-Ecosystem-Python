# Phase 2 — LangChain Integrations

**Status:** 🗒️ Topic list only — `doc.md`/`code.py` not built yet. Ask for this phase by
name to have it fully built out, following the same pattern as
[Phase 0](../phase-0-foundations/) and [Phase 1](../phase-1-langchain-fundamentals/).

**Teaching point for this whole phase:** don't teach integrations as isolated APIs —
teach the abstraction (`init_chat_model`, `Document`, `VectorStore`, `Retriever`) once,
then show how different providers implement it.

## Topics

01. **Model Integration Pattern** — one interface (`init_chat_model` / `BaseChatModel`), many providers; how swapping providers changes zero application code.
02. **Provider Walkthrough: OpenAI, Anthropic, Gemini** — auth, model params, streaming, cost/latency tradeoffs across the three.
03. **Local & Alternative Providers** — Ollama (local, private, free) and OpenRouter (provider-agnostic routing).
04. **Document Loaders — Common Formats** — PDF, web pages, CSV, JSON, Markdown, SQL database rows as `Document` objects.
05. **External Data Integrations** — Google Drive, Notion, GitHub, Slack/generic REST APIs as data sources.
06. **Vector Store Integration Pattern** — Chroma, FAISS, Qdrant, Pinecone, pgvector behind the same `VectorStore` interface.
07. **Choosing a Vector Database** — local vs managed, cost, filtering, scale, hybrid-search support — decision framework.
08. **Mini Project: Multi-Source Connector** — one ingestion pipeline that normalizes PDF + web + Notion into the same `Document` schema and loads it into a chosen vector store.

## Phase project

**Multi-Source Connector** — a single ingestion script that pulls from 2–3 heterogeneous
sources, normalizes to `Document`s with consistent metadata, and writes to a vector
store chosen using the Phase 2 decision framework.
