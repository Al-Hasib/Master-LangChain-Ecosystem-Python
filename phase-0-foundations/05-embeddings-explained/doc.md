# 05 — Embeddings Explained

## Problem

Keyword search misses paraphrases ("car" vs "automobile"). Viewers need to understand
*why* semantic search works before Phase 3 (RAG) asks them to trust it.

## Concept

An **embedding** is a fixed-length vector of numbers (e.g. 1536 floats) produced by an
embedding model from a piece of text, such that texts with similar *meaning* end up as
vectors that are close together in that high-dimensional space, regardless of exact
wording.

```text
"a dog barking"      -> [0.12, -0.04, 0.88, ...]
"a puppy makes noise" -> [0.14, -0.02, 0.85, ...]   (close to the above)
"quarterly tax filing" -> [-0.71, 0.33, 0.02, ...]  (far from both)
```

"Close" is measured with a similarity metric — most commonly **cosine similarity**
(angle between vectors, ignoring magnitude) or dot product. This is the mechanism behind
"semantic search": embed the query, embed the documents, rank documents by similarity to
the query vector.

Important properties to internalize:
- Embeddings capture *meaning*, not *facts* — an embedding model can't tell you an
  embedded statement is true, only that it's semantically similar to your query.
  Text and query embeddings must come from the **same embedding model family** to be
  meaningfully comparable.
- Embedding models are separate from chat models (though some providers offer both) and
  are typically much cheaper per call.

## Minimal code

`code.py` embeds a handful of short sentences plus a query, computes cosine similarity
between the query and each sentence, and prints them ranked — you'll see the
semantically related sentence rank above lexically similar but semantically unrelated
ones.

## Production notes

Pick one embedding model for a given vector store and never mix — re-embedding
everything is required if you switch models. Embedding dimension and cost both vary by
model; smaller embedding models are often "good enough" and much cheaper at scale.

## Debugging

- Similarity scores all clustered close together with no clear winner → often a sign
  your texts are too short/generic, or you're comparing across different embedding
  models.
- Retrieval "feels wrong" → check you're not accidentally embedding with one model and
  querying with another.

## Mini challenge

Add a sentence that's *lexically* similar to the query (shares many words) but
semantically unrelated, and one that's lexically different but semantically related.
Confirm cosine similarity ranks by meaning, not word overlap.
