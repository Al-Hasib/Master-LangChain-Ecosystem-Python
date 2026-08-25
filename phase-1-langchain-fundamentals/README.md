# Phase 1 — LangChain Fundamentals

**Goal:** rebuild everything from Phase 0's mini project using LangChain's
abstractions, so viewers feel the reduction in code directly, then go further into
`create_agent`, middleware, and streaming — the actual start of "the LangChain course."

**Status:** ✅ Fully built — every topic has `doc.md` and `code.py`.

Uses the current LangChain agent API centered on `init_chat_model` and `create_agent`
(see [docs.langchain.com/oss/python/langchain/overview](https://docs.langchain.com/oss/python/langchain/overview)).

## Topics

01. [What is LangChain? & Architecture](01-what-is-langchain-and-architecture/doc.md) — the framework's layers and why they exist.
02. [Models & `init_chat_model`](02-models-and-init-chat-model/doc.md) — one call to swap providers/models with zero other code changes.
03. [Messages, Prompts & Prompt Templates](03-messages-prompts-and-templates/doc.md) — LangChain's `Message` objects and reusable, parameterized prompts.
04. [Structured Output](04-structured-output/doc.md) — `with_structured_output` and Pydantic schemas.
05. [Tools & Tool Calling](05-tools-and-tool-calling/doc.md) — the `@tool` decorator and how models pick tools.
06. [`create_agent` & the Agent Loop](06-create-agent-and-agent-loop/doc.md) — replacing Phase 0's hand-written tool loop with one call.
07. [Agent State & Runtime Context](07-agent-state-and-runtime-context/doc.md) — what the agent tracks between steps and how to pass it config/context.
08. [Middleware, Retries, Fallbacks & Guardrails](08-middleware-retries-fallbacks-guardrails/doc.md) — hooking into the agent loop and making it resilient.
09. [Streaming Responses](09-streaming-responses/doc.md) — token and step streaming from a chat model and an agent.
10. [LangChain Project Structure](10-langchain-project-structure/doc.md) — organizing a real, multi-file LangChain application.
11. [Mini Project: AI Research Assistant v1](11-mini-project-research-assistant/doc.md) — an agent with calculator, web search, and date/time tools.

## Phase project

**AI Research Assistant v1**

```text
User
  ↓
LangChain Agent
  ↓
LLM
  ↓
Tools
 ├── Calculator
 ├── Web Search
 └── Date/Time
```

## Running the examples

```bash
pip install -r ../requirements.txt
cp ../.env.example ../.env   # fill in OPENAI_API_KEY at minimum
python 01-what-is-langchain-and-architecture/code.py
```
