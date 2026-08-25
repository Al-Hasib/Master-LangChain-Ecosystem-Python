# 02 — Tracing & Trace Hierarchy

## Problem

"It gave the wrong answer" doesn't tell you *why*. Was the retrieval step returning bad
context? Did the model ignore good context? Did a tool call fail silently? A flat log
line can't answer that — you need to see the actual **tree of calls** that produced the
final answer, in order, with each step's input/output visible.

## Concept

A LangSmith trace is a tree. The **root run** is whatever you called from your code
(`agent.invoke(...)`, a chain's `.invoke(...)`, a plain traced function). Every LLM call,
tool call, retriever call, or `@traceable`-decorated function invoked underneath becomes
a **child run**, nested under whichever run called it — exactly mirroring your actual
call stack.

Two ways a run gets added to the tree:

1. **Automatically** — any LangChain/LangGraph construct (`ChatOpenAI`, `create_agent`,
   a retriever, a chain built with `|`) traces itself with zero extra code, as long as
   tracing is on (Topic 01).
2. **Explicitly** — wrap a plain Python function with `@traceable` from `langsmith` to
   put it in the tree too. This is what turns "some Python code called the agent" into
   "a readable step in the trace" for logic that isn't a LangChain object itself
   (retrieval glue, pre/post-processing, custom scoring).

```python
from langsmith import traceable

@traceable(run_type="retriever")
def retrieve(question: str) -> list[str]:
    return [doc.page_content for doc in vectorstore.similarity_search(question, k=2)]

@traceable(run_type="chain")
def rag_answer(question: str) -> str:
    context = retrieve(question)          # becomes a child run automatically
    return model.invoke(f"{context}\n\n{question}").content   # also becomes a child run
```

Calling `rag_answer(...)` produces this shape in the LangSmith UI:

```text
rag_answer                    (root run, run_type=chain)
├─ retrieve                   (child, run_type=retriever)
│   └─ Chroma similarity_search  (auto-traced by the vector store integration)
└─ ChatOpenAI                 (child, run_type=llm - auto-traced, shows the exact
                                prompt sent and tokens used)
```

Reading the tree: **latency and token cost roll up** — the root run's total latency is
the sum of its children's, so the slowest child is your bottleneck. **Inputs/outputs are
visible per node** — if `retrieve` returned empty context, you'll see that node's output
is `[]` before you even look at what the LLM said, which immediately tells you the bug is
upstream of the model, not in the model.

## Minimal code

`code.py` builds this course's smallest possible RAG pipeline, entirely in-code (Chroma,
in-memory, no dependency on any other phase's files) — this doubles as the **Phase 9
project**: a small RAG agent instrumented end-to-end. `retrieve` and `rag_answer` are
both `@traceable`; `rag_answer` calls `retrieve` then an auto-traced `ChatOpenAI` call, so
running it produces the exact three-level tree diagrammed above, live, in your LangSmith
project (if a key is configured).

## Production notes

- Give every `@traceable` function a `run_type` (`"retriever"`, `"chain"`, `"tool"`,
  `"llm"`) — it drives which icon/columns the UI shows and which token/latency rollups
  apply.
- Attach `metadata={"user_id": ..., "session_id": ...}` to `@traceable` calls (via
  `langsmith.trace(...)` context or the decorator's `metadata` kwarg) so you can filter
  the trace list by customer/session in production, not just browse chronologically.
- Nest deliberately — don't `@traceable` every one-line helper; trace at the granularity
  you'd actually want to click into when debugging (retrieval, generation, tool calls —
  not string formatting).

## Debugging

- A child run is missing from the tree entirely → it wasn't a LangChain/LangGraph
  object and wasn't wrapped in `@traceable` — plain Python calls are invisible to tracing
  by default.
- The tree looks flat (no nesting) when you expected nesting → the inner function was
  called *outside* the traced context (e.g., in a different thread/process without
  context propagated) — `@traceable` uses context vars to know "what's my parent," and
  that context doesn't cross thread boundaries for free.
- One child run dominates total latency → that's your optimization target, not the root.

## Mini challenge

Add a third `@traceable` step — e.g. a `rerank` function between `retrieve` and the
final model call — and confirm it shows up as a sibling of `retrieve`, nested under the
same `rag_answer` root, in the order it actually ran.
