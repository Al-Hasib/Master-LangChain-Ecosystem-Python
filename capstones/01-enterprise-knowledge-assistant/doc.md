# Capstone 01 — Enterprise Knowledge Assistant (Production RAG)

## What this proves

This is the "boring but correct" RAG stack that most real internal tools actually need:
chunk a mixed-source document set, embed it, retrieve it, **grade what came back before
trusting it**, answer with citations tied to real metadata (not the model's word for it),
and carry conversation context across a short back-and-forth. None of these ideas is
individually hard — the point of this capstone is proving they compose into one
coherent, inspectable pipeline instead of a single opaque `retriever | llm` chain that
silently hallucinates when retrieval comes back empty or off-topic.

The portfolio-relevant skill on display: this is what separates a RAG demo from a RAG
system a team could actually trust — grounding is checked, not assumed, and every claim
in the answer can be traced back to a `source_name` in the corpus.

## Draws on

- Phase 3 Topic 02 — Document Loaders & Document objects (`page_content` + `metadata`)
- Phase 3 Topic 03 — Text splitting & chunking strategies
- Phase 3 Topic 04 — Embeddings & vector stores
- Phase 3 Topic 05 — Retrievers & similarity search
- Phase 3 Topic 06 — Metadata filtering (via `source_type` on every chunk)
- Phase 3 Topic 07 — Building a basic RAG pipeline with sources/citations
- Phase 4 Topic 07 — Document relevance grading & self-correction (the grading step here
  is the simple, single-pass version of that idea — see "What's simplified")
- Phase 2 Topic 08's normalized-metadata pattern (`source_type` / `source_name` /
  `origin`), reused here for the policy vs. handbook corpus

## Architecture

```text
In-code corpus (policy + handbook docs, normalized metadata)
        │
        ▼
RecursiveCharacterTextSplitter          <- Phase 3 Topic 03
        │
        ▼
OpenAIEmbeddings -> Chroma collection    <- Phase 3 Topic 04
        │
        ▼
retriever.invoke(question)  (top-k)      <- Phase 3 Topic 05
        │
        ▼
Relevance grader (structured output,     <- Phase 4 Topic 07 (simplified)
per-chunk: is this chunk grounded
enough to answer the question?)
        │
   ┌────┴────┐
 pass      fail -> chunk dropped, never reaches the prompt
   │
   ▼
Answer generation, citing kept chunks    <- Phase 3 Topic 07
by [source_name], appended to a running
conversation-memory list
        │
        ▼
Answer + Sources
```

## Running it

```bash
cd capstones/01-enterprise-knowledge-assistant
python code.py
```

Requires `OPENAI_API_KEY` in `../.env` (copy `../.env.example` if you haven't already).
No external files or services are needed — the corpus, the questions, and the whole
pipeline run in-process against the OpenAI API only.

## What's simplified vs. a real production version

- **Grading is single-pass, not a re-retrieval loop.** A real self-corrective pipeline
  (Phase 4 Topic 07) would re-query or re-rewrite the question when *everything* gets
  graded irrelevant. Here, if every retrieved chunk fails the grade, the assistant just
  says so honestly instead of guessing — good enough to prove the grounding check works,
  but not the full self-correction loop (that's Capstone 02's job).
- **Conversation memory is a plain Python list**, not `Chroma`-backed long-term memory or
  a summarizing buffer. It's enough to show the assistant using prior turns, not enough
  for a long-running multi-session assistant.
- **The corpus is small and lives in code** (12 short documents) so the example runs
  standalone with no files/services beyond the OpenAI API — a real deployment would
  ingest hundreds of PDFs/Confluence pages/etc. via the loaders in Phase 3 Topic 02.
- **No reranking, hybrid search, or evaluation harness** (Phase 4 Topics 03/04/08,
  Phase 9) — this capstone is retrieval + grading + citation only.
- **Chroma runs in-memory (ephemeral client)** — a real deployment would persist it or
  use a hosted vector DB.

## Extend it further

- Swap the single-pass grader for the real self-corrective loop: on an all-irrelevant
  grade, rewrite the question and retry retrieval once before giving up (Phase 4 Topic 07).
- Add a second retriever filtered by `source_type` and let the assistant pick which one
  to search based on the question (a preview of Capstone 02's agentic retrieval).
- Persist the Chroma collection to disk and add a LangSmith-traced evaluation dataset
  (Phase 9) that checks citation accuracy across a fixed set of questions.
