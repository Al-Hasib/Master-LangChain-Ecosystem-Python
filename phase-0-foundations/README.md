# Phase 0 — AI Application Foundations

**Goal:** make sure viewers understand LLM-application concepts *before* touching
LangChain, so the rest of the course reads as "here's how LangChain implements the thing
you already understand" rather than "memorize this API."

**Status:** ✅ Fully built — every topic has `doc.md` (video script/notes) and `code.py`
(runnable example) using raw provider SDKs (no LangChain yet — that starts in Phase 1).

## Topics

01. [What is an LLM Application?](01-what-is-llm-application/doc.md) — LLM vs Chat Model vs AI Agent, in one topic.
02. [Tokens, Context Windows & Model Parameters](02-tokens-context-and-parameters/doc.md) — tokenization, context limits, temperature/top_p/max_tokens.
03. [Messages & Roles](03-messages-and-roles/doc.md) — system/user/assistant messages and conversation state.
04. [Structured Output & Function/Tool Calling](04-structured-output-and-function-calling/doc.md) — getting reliable JSON and letting the model request actions.
05. [Embeddings Explained](05-embeddings-explained/doc.md) — turning text into vectors, and what "similar" means.
06. [Vector Databases Explained](06-vector-databases-explained/doc.md) — why you need one, and how similarity search works at scale.
07. [RAG vs Agent vs Workflow](07-rag-vs-agent-vs-workflow/doc.md) — what is RAG, what is an agent, and the spectrum between "fixed pipeline" and "autonomous loop."
08. [Architecture of a Modern AI App & Mini Project](08-architecture-and-mini-project/doc.md) — putting the pieces together, then building a tiny app directly against a provider API (no framework).

## Mini project

**Tiny LLM app, no framework** — a small CLI that takes a question, calls a chat model
directly via its SDK, and prints a structured answer. Everything here gets replaced by
LangChain abstractions starting in Phase 1 — the point is knowing what's being
abstracted.

## Running the examples

```bash
pip install -r ../requirements.txt
cp ../.env.example ../.env   # fill in OPENAI_API_KEY at minimum
python 01-what-is-llm-application/code.py
```
