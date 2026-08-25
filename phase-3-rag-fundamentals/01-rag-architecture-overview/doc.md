# 01 — RAG Architecture Overview

## Problem

Chat models only know what was in their training data, and they'll confidently answer
questions about your private/current data anyway — by making it up. Phase 0 Topic 07
named **RAG (Retrieval-Augmented Generation)** as one of the three application shapes
and sketched it in a few lines. Phase 3 builds it for real: this topic is the minimal
end-to-end version everything else in the phase refines.

## Concept

RAG is a **2-step workflow** (Phase 0 Topic 07's fixed-pipeline shape, not an agent
decision): **retrieve**, then **generate**.

```text
1) RETRIEVE                                   2) GENERATE
Question -> embed -> vector search             [question + retrieved docs] -> LLM -> Answer
            (Phase 0 Topic 05: embeddings)
            (Phase 0 Topic 06: vector DB)
```

Step 1 reuses exactly what Phase 0 Topics 05–06 explained conceptually: embed the
question with the same embedding model used on the documents, run a similarity search,
get back the top-k most relevant chunks. Step 2 "stuffs" those chunks into a prompt as
context and asks the LLM to answer *using* them — the same `prompt | model` LCEL chain
from Phase 1 Topic 03, just with a context variable filled in from retrieval instead of
by hand.

Why this fixes two things at once:
- **Knowledge cutoff** — the retrieved documents can be as current as your ingestion
  pipeline, regardless of when the model was trained.
- **Hallucination on facts outside training data** — the model is answering from text
  that's literally in front of it, not from parametric memory alone.

RAG being "always retrieve, then always generate" is exactly the workflow vs. agent
distinction from Phase 0 Topic 07 — the model never decides *whether* to retrieve here.
Letting the model decide that is Agentic RAG, covered in Phase 5.

This topic uses a tiny **in-code** corpus (a Python list of strings turned into
`Document` objects by hand) so the retrieve/generate mechanics are visible without any
loader machinery — real files and the `Document` object's shape are Topic 02.

## Minimal code

`code.py` wraps five facts about a fictional outdoor-gear company in `Document` objects,
embeds them into an in-memory Chroma store (Phase 2 Topic 06's `.from_documents` /
`.similarity_search` pattern), then answers two questions: one the corpus can answer,
and one it can't — showing retrieval-then-generation end to end, including the case
where retrieval legitimately comes up empty of useful content.

## Production notes

Everything here runs in memory and rebuilds the vector store on every run — fine for a
demo, not for a real app. Topic 04 covers persisting the store so you embed once, not
every process start. Also note: nothing here strips retrieval before generation just
because a question doesn't need it — that inefficiency is intentional (fixed workflow),
and Phase 0 Topic 07's mini challenge is exactly about noticing it.

## Debugging

- Model answers confidently even for the out-of-corpus question → the prompt doesn't
  instruct it to stick to context; add "answer only using the provided context, and say
  so if the context doesn't contain the answer."
- Retrieved chunks look irrelevant → with only 5 tiny documents this is usually a sign
  the demo corpus is too small/generic to show real ranking behavior — expected at this
  scale, real corpora (Topic 07) behave better.

## Mini challenge

Change the prompt to *not* say "use only the provided context" and re-run the
out-of-corpus question — watch the model fall back to its own (unverifiable) general
knowledge instead of admitting it doesn't know.
