# 07 — Document Relevance Grading & Self-Correction

## Problem

Every technique so far (Topics 02–06) makes retrieval *better*, but none of them make it
*checked*. A retriever always returns its top-k — "best of k" isn't the same as "good."
When a query falls outside what the corpus actually covers well, top-k still returns
*something*, and Topic 01 already showed what happens next: the model faithfully builds
an answer out of documents that don't actually support it.

## Concept

Grade every retrieved document with a structured, binary relevance check *before* it
reaches generation — an LLM call per document, asking "is this actually relevant to the
question," with a Pydantic-enforced true/false output so it's programmatically
filterable rather than prose you have to parse:

```python
from pydantic import BaseModel, Field

class RelevanceGrade(BaseModel):
    relevant: bool = Field(description="True if the document helps answer the question")
    reason: str

grader = model.with_structured_output(RelevanceGrade)
grade = grader.invoke(f"Question: {question}\n\nDocument: {doc.page_content}")
```

Filter to only the documents graded relevant. If **none** survive the filter, that's a
signal the original query/retrieval combination failed outright — rather than generating
from nothing (or from irrelevant docs anyway), **re-query once**: rewrite the query
(Topic 02's technique) and retrieve again before giving up.

```text
retrieve(query) ──> grade each doc ──> any relevant? ──yes──> generate from relevant docs
                                              │
                                              no
                                              ▼
                                 rewrite query, retrieve ONCE more
                                              │
                                              ▼
                                 grade again ──> generate from whatever survives
                                 (or answer "not found in knowledge base" if still empty)
```

This is a simplified, linear version of the grading/self-correction loop popularized by
CRAG and Self-RAG-style patterns — here it's a plain Python function with a hard retry
cap of 1, not an agentic loop. A fully agentic version that can retry indefinitely and
branch on more complex conditions belongs in Phase 6 (LangGraph), where cycles and
conditional edges are first-class.

## Minimal code

`code.py` runs grading against a query that only partially overlaps the Nimbus corpus,
showing the grader filtering out irrelevant retrieved docs, triggering one re-query when
nothing survives, and generating only from what's actually graded relevant.

## Production notes

Project C (Multi-Document Enterprise RAG) uses grading as a QC gate after ensemble
retrieval (Topic 06) — the more sources and retrievers feeding into one candidate set,
the more noise grading needs to filter before generation ever sees it. Grading costs one
LLM call per retrieved document; at scale, run the grading calls concurrently rather than
in a loop (`asyncio.gather` over `.ainvoke`) to keep latency down.

## Debugging

- Grader marks everything relevant regardless of content → the grading prompt is too
  permissive; give it a strict rubric ("relevant only if it directly helps answer the
  specific question, not just topically related") and a few contrastive examples.
- Infinite re-query loops → always cap retries (this example caps at 1); an ungrounded
  answer after the cap is better than a hung pipeline.
- Re-query never changes the outcome → the rewritten query needs to meaningfully differ
  from the original (Topic 02's rewriting technique), not just be a light rephrase.

## Mini challenge

Lower the grading threshold from "binary relevant/not" to a 0–10 score and require a
minimum score (e.g. 6) to pass — compare which documents flip between "barely relevant"
and "not relevant" versus the binary version.
