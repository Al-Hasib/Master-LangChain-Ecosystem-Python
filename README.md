# Master LangChain Ecosystem — YouTube Course

A problem-centric, phase-by-phase curriculum for a YouTube course/playlist covering the
full modern LangChain ecosystem: **LangChain → RAG → Agents → LangGraph → Deep Agents →
LangSmith → Production**.

This repo is the source-of-truth for the course: one folder per phase, one folder per
topic inside each phase, and (where built out) a `doc.md` + `code.py` pair per topic —
`doc.md` is the script/notes for the video, `code.py` is the runnable example to record
on screen.

> Curriculum is **condensed to ~60–70 lessons** (not the raw ~195 micro-topic map some
> planning tools produce) — closely related micro-topics are merged into single, meatier
> lessons that match a realistic 10–25 minute video.

## Status

| Phase | Folder | Status |
|---|---|---|
| 0 — Foundations | [`phase-0-foundations/`](phase-0-foundations/) | ✅ Fully built (doc + code) |
| 1 — LangChain Fundamentals | [`phase-1-langchain-fundamentals/`](phase-1-langchain-fundamentals/) | ✅ Fully built (doc + code) |
| 2 — Integrations | [`phase-2-integrations/`](phase-2-integrations/) | 🗒️ Topic list only |
| 3 — RAG Fundamentals | [`phase-3-rag-fundamentals/`](phase-3-rag-fundamentals/) | 🗒️ Topic list only |
| 4 — Advanced RAG | [`phase-4-advanced-rag/`](phase-4-advanced-rag/) | 🗒️ Topic list only |
| 5 — Agentic RAG | [`phase-5-agentic-rag/`](phase-5-agentic-rag/) | 🗒️ Topic list only |
| 6 — LangGraph | [`phase-6-langgraph/`](phase-6-langgraph/) | 🗒️ Topic list only |
| 7 — Advanced Agents | [`phase-7-advanced-agents/`](phase-7-advanced-agents/) | 🗒️ Topic list only |
| 8 — Deep Agents | [`phase-8-deep-agents/`](phase-8-deep-agents/) | 🗒️ Topic list only |
| 9 — LangSmith | [`phase-9-langsmith/`](phase-9-langsmith/) | 🗒️ Topic list only |
| 10 — Production AI Engineering | [`phase-10-production/`](phase-10-production/) | 🗒️ Topic list only |
| Capstones | [`capstones/`](capstones/) | 🗒️ Topic list only |

To build out a "topic list only" phase, ask for it by name — it follows the same
`doc.md` + `code.py` per topic pattern as Phases 0–1.

## Learning progression (problem-centric, not technology-centric)

```text
AI APPLICATION ENGINEERING
        │
  ┌─────┴─────┐
KNOWLEDGE    ACTION
  (RAG)     (AGENTS)
  │              │
  └──────┬───────┘
      LANGGRAPH  (orchestration/runtime)
         │
   DEEP AGENTS   (planning + subagents harness)
         │
     LANGSMITH   (trace / eval / observe)
         │
     PRODUCTION  (deploy / scale / secure)
```

Each phase answers "why does this technology exist?" before showing the API.

## The one evolving project

Instead of unrelated toy demos, one application evolves across phases:

```text
Simple Chatbot → Document Q&A → Production RAG → Agentic RAG →
LangGraph Research Agent → Multi-Agent Research System →
Deep Research Agent → Production AI Application
```

## Video format (used per topic doc.md)

1. **Problem** (2–5 min) — what breaks / what's missing without this
2. **Concept** (5–10 min) — the architecture, in plain terms
3. **Minimal code** (5–15 min) — smallest possible working example → `code.py`
4. **Production notes** (10–20 min) — how this looks for real
5. **Debugging** (5–10 min) — common failure modes
6. **LangSmith** (3–5 min, where relevant) — trace/eval view
7. **Mini challenge** — a prompt for the viewer to extend the example

## Tech stack (standardized across the whole course)

- **Language:** Python 3.11+
- **Frameworks:** LangChain, LangGraph, Deep Agents
- **Observability:** LangSmith
- **Models:** OpenAI (primary), Anthropic (alternative), Ollama (local)
- **Vector DB:** Chroma / FAISS to start; Qdrant / pgvector shown later
- **Database:** PostgreSQL
- **API layer:** FastAPI
- **Frontend (later phases):** Streamlit → custom web frontend
- **Deployment:** Docker, LangSmith Deployment

## Repo conventions

```text
phase-N-<name>/
  README.md              # topic list + phase-level project(s) for this phase
  NN-<topic-slug>/
    doc.md                # video script/notes: Problem → Concept → Code walk-through
    code.py                # standalone, runnable example (guarded __main__, .env driven)
```

Every `code.py` is written to run standalone with `python code.py` given a populated
`.env` (see `.env.example`). Examples fail with a clear message rather than a stack
trace when an API key is missing.

## Setup

```bash
python -m venv .venv
. .venv/Scripts/activate      # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
cp .env.example .env          # then fill in your API keys
```

## Suggested playlist split (for publishing, not for this repo's folder layout)

1. **LangChain Complete Course — Foundations** — Phases 0–1
2. **LangChain RAG Complete Course** — Phases 3–4
3. **LangChain Agents Complete Course** — parts of Phase 1 + Phases 5, 7
4. **LangGraph Complete Course** — Phase 6
5. **Deep Agents Complete Course** — Phase 8
6. **LangSmith Complete Course** — Phase 9
7. **Production AI Engineering** — Phase 10
8. **LangChain Real-World Projects** — Capstones

Reference docs kept in sync with: LangChain overview, retrieval/RAG guide, LangGraph
overview, Deep Agents quickstart, LangSmith docs (all at docs.langchain.com).
