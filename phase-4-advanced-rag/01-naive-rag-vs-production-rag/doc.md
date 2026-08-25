# 01 — Naive RAG vs Production RAG

## Problem

Phase 3 built the basic pipeline: chunk documents, embed them, `similarity_search(query,
k)` at query time, stuff the top-k chunks into a prompt, generate. It works great on the
kind of tidy demo corpus Phase 3 used. It breaks — quietly, not with an exception — the
moment your corpus looks like a real one: many documents, overlapping topics, facts that
live in different places than the words used to ask about them.

This topic catalogues *how* it breaks, with one concrete example, so the rest of Phase 4
reads as "here's the fix for failure mode N" instead of a grab-bag of retriever classes.

## Concept

Five failure modes of naive top-k similarity search, and which later topic fixes each:

| # | Failure mode | What it looks like | Fixed by |
|---|---|---|---|
| 1 | Ambiguous/underspecified query | "Am I eligible?" — eligible for what? | Topic 02 (query transformation) |
| 2 | Irrelevant chunks mixed into top-k | A chunk that shares vocabulary but not meaning crowds out the real answer | Topic 03 (compression & reranking) |
| 3 | Exact-term / acronym queries | Dense embeddings represent *meaning*, not exact tokens — an error code or SKU barely moves the embedding | Topic 04 (hybrid search) |
| 4 | Lost context across chunk boundaries | The fact that actually answers the question is split across two chunks; top-k grabs one and misses the other | Topic 05 (parent-document retrieval) |
| 5 | Silently wrong answer from bad retrieval | Nothing checks whether what was retrieved (or generated) is actually relevant/grounded | Topics 07–08 (grading & groundedness) |

This topic demonstrates **failure mode 4** end-to-end, because it's the easiest one to
see with a single query and it motivates the rest of the phase.

```text
naive pipeline:
  query -> embed -> similarity_search(k=2) -> [chunk A, chunk B] -> stuff into prompt -> LLM -> answer
                                                    ^
                                    the fact that overrides the general rule
                                    lives in chunk C, which never made top-k
```

**The example:** Nimbus (our running example company) has a general refund policy *and*
a separate, differently-worded exception for its enterprise "Apollo" plan. The exception
doesn't use the word "refund" — it talks about "annual enterprise contracts" and a
"Master Services Agreement." A naive top-k search, biased toward chunks that lexically
and semantically resemble the query, retrieves the general policy and the Apollo plan's
*feature* description, but not the override rule. The model — grounded faithfully in
what it *was* given — confidently states the wrong policy.

This is not a hallucination in the usual sense: the model didn't make anything up, and
it was told to answer only from context. The retrieval step failed; the generation step
just faithfully reported that failure.

## Minimal code

`code.py` builds a 7-document Nimbus knowledge base (deliberately including the
fragmented refund-exception fact), runs the exact naive pipeline described above against
the query `"I'm on the Apollo plan and want a refund — am I eligible?"`, prints what got
retrieved and the generated answer, then prints the document that never made top-k and
explains why the answer is unreliable even though the model "followed the rules."

## Production notes

Naive RAG isn't wrong to start with — it's the right first version, and it's what
Projects A/B/C in this phase all still use as their retrieval *base*. The point isn't
"never use plain `similarity_search`" — it's "know its failure modes so you can tell
when your corpus has outgrown it." A 10-document FAQ probably never needs Topics 02–08.
A 10,000-document enterprise knowledge base (Project C) needs most of them.

## Debugging

- Answer is confidently wrong, and the model *did* cite the retrieved context correctly
  → the retrieval, not the generation, is the bug. Print `retriever.invoke(query)` (or
  `similarity_search`) directly and read what actually came back before touching the
  prompt.
- Increasing `k` "fixes" one query and breaks the next → you're compensating for
  precision loss with recall, which just re-introduces failure mode 2 (irrelevant
  chunks). This is exactly why Topics 02–05 exist instead of "just retrieve more."

## Mini challenge

Re-run `code.py` with `k` set to the full corpus size (retrieve everything). Confirm the
missing fact is now included — then look at how much irrelevant text also came along for
the ride, and consider what that costs at 10,000 documents instead of 7.
