# 04 — Query Planning

## Problem

Topic 03's agent handles a question needing two tools by chaining tool calls inside its
own loop — but that chaining is implicit, hidden inside the model's reasoning. For a
genuinely compound question ("What's Aurora's return policy, what's the status of Maria
Lopez's latest order, and what is LangGraph used for?"), letting the model juggle three
unrelated sub-problems in one pass is asking a lot: it can lose track of a clause, answer
two of three parts, or blend contexts across sub-questions. Splitting the question
explicitly, *before* any retrieval happens, fixes that.

## Concept

Query planning adds one **fixed** step in front of the agent: decompose the compound
question into independent sub-questions with structured output (Phase 1 Topic 04), then
run each sub-question through the Topic 03 multi-tool agent separately, then synthesize
one final answer from the sub-answers.

```text
Compound question
        │
        ▼
 LLM + with_structured_output(SubQuestions)   <-- FIXED step, not agent-decided
        │
        ▼
 ["sub-q 1", "sub-q 2", "sub-q 3"]
        │            │            │
        ▼            ▼            ▼
   multi-tool    multi-tool    multi-tool     <-- Topic 03's agent, run per sub-question
     agent          agent         agent           (still decides its OWN tool per sub-q)
        │            │            │
        └──────┬─────┴──────┬─────┘
               ▼             ▼
          synthesis LLM call -> one final answer
```

Notice the two layers of "who decides": decomposition is a **workflow** step (always
runs, same way, every time) while tool selection *within* each sub-question is still
**agent-directed** (Topic 03's logic, unchanged). This mix — fixed step wrapping agent
steps — is exactly what Topic 06 formalizes as "Hybrid RAG."

## Minimal code

`code.py` defines a `SubQuestions` Pydantic model (`list[str]`) and uses
`model.with_structured_output(SubQuestions)` to decompose a three-part question. Each
sub-question is run through Topic 03's multi-tool agent (vector + SQL + web), and a final
LLM call synthesizes the sub-answers into one coherent response.

## Production notes

Decomposition isn't free — it's an extra LLM call, and for genuinely simple questions
it's pure overhead (a one-part question "decomposes" into itself, wasting a round trip).
Gate this: only run the decomposition step when a heuristic (question length, presence
of "and"/multiple question marks) or a cheap classifier suggests the question is
compound — or just let the agent from Topic 03 handle simple questions directly and only
route compound-looking ones through this pipeline.

## Debugging

- Decomposition produces sub-questions that overlap or contradict → tighten the
  decomposition prompt to explicitly ask for *independent, non-overlapping* questions.
- Synthesis step "loses" one sub-answer → make sure the synthesis prompt is given ALL
  sub-question/sub-answer pairs explicitly labeled, not just concatenated free text.

## Mini challenge

Feed the pipeline a question that's actually simple ("What's Aurora's return policy?")
and observe `SubQuestions` returning a list of length one — confirming decomposition
degrades gracefully instead of forcing artificial splits.
