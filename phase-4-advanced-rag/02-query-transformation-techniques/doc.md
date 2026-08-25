# 02 — Query Transformation Techniques

## Problem

Topic 01's Apollo refund query failed for a specific reason: the query's wording
("refund", "eligible") never overlapped with the override fact's wording ("annual
enterprise contracts", "Master Services Agreement"). The user's words and the answer's
words are different words for the same idea. Naive retrieval searches with the query
*as typed* — if that phrasing is ambiguous, underspecified, or just lexically distant
from the answer, top-k search never gets a chance to find it.

## Concept

Three techniques that transform the query *before* it hits the vector store, each
attacking the mismatch differently:

**1. Query rewriting.** Ask an LLM to rewrite the user's query into a more explicit,
retrieval-friendly form before searching — expanding abbreviations, naming the entities
involved, adding likely synonyms.

```text
"I'm on the Apollo plan and want a refund - am I eligible?"
        │  LLM rewrite
        ▼
"Apollo enterprise plan refund eligibility, annual contract cancellation policy,
 Master Services Agreement exceptions"
```

**2. Multi-query retrieval.** Instead of rewriting to *one* better query, ask an LLM to
generate several differently-phrased variants of the question, retrieve for each
variant, and take the union of results. Different phrasings surface different chunks —
this is a precision/recall trade in favor of recall.
`langchain_classic.retrievers.multi_query.MultiQueryRetriever` automates exactly this:

```python
from langchain_classic.retrievers.multi_query import MultiQueryRetriever

mq_retriever = MultiQueryRetriever.from_llm(retriever=vectorstore.as_retriever(), llm=llm)
docs = mq_retriever.invoke(query)  # runs N generated variants, merges + dedupes results
```

**3. HyDE (Hypothetical Document Embeddings).** Instead of embedding the terse query,
ask an LLM to *write a hypothetical answer* to the question — even though it might get
details wrong — and embed *that* instead. A fabricated answer paragraph is stylistically
much closer to how the real answer is written in your docs than a short question is,
which often makes it a better anchor for similarity search.

```text
query -> LLM "imagine the answer" -> hypothetical answer paragraph -> embed THIS -> similarity_search
```

All three exist because the assumption naive RAG makes — "the query's embedding will
land near the answer's embedding" — is often false for short, ambiguous, or
differently-worded questions. These techniques change *what gets embedded*, not the
vector store or the generation step.

## Minimal code

`code.py` re-runs Topic 01's Apollo refund query four ways — naive (baseline), rewritten
query, multi-query, and HyDE — against the same Nimbus corpus, and prints whether each
technique's retrieved set includes the override-fact document that naive search missed.

## Production notes

Multi-query and HyDE both cost extra LLM calls *before* retrieval even starts — this is
a latency/cost trade you're making deliberately for recall. In practice these are paired
with Topic 03's reranking/compression, because casting a wider net (multi-query
especially) pulls in more irrelevant candidates alongside the useful ones — Project A
(Research Paper RAG) uses hybrid search + reranking for exactly this reason, downstream
of whichever query transformation is in play.

## Debugging

- Multi-query variants come back nearly identical → the rewrite LLM is being too
  conservative at low temperature; give it a slightly higher temperature or an explicit
  instruction to vary phrasing/angle, not just synonyms.
- HyDE retrieval gets *worse* → the hypothetical answer invented specific wrong details
  (a number, a name) that pulled the embedding toward an unrelated real document. Keep
  the hypothetical short and generic rather than encouraging specificity.
- Query rewriting drops necessary detail (e.g. strips "Apollo" entirely) → the rewrite
  prompt needs to preserve named entities from the original query, not just paraphrase.

## Mini challenge

Combine two techniques: rewrite the query first, then feed the rewritten query into
`MultiQueryRetriever` instead of the original. Compare the retrieved set against running
each technique alone.
