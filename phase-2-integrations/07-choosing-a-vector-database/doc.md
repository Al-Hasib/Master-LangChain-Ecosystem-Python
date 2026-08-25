# 07 — Choosing a Vector Database

## Problem

Topic 06 proved switching backends is cheap *technically*. That doesn't tell you which
one to reach for *first* — teams waste time either over-engineering (Pinecone for a
500-document prototype) or under-provisioning (FAISS for a 50-million-vector production
system with concurrent writes).

## Concept

Five questions settle most of the decision:

1. **Scale** — thousands of vectors (any local store is fine) vs. millions+ (need a
   store built for distributed/approximate search at scale).
2. **Ops appetite** — willing to run/manage infrastructure (self-hosted Qdrant,
   pgvector-on-Postgres you already run) vs. want zero-ops (Pinecone, a managed Qdrant
   Cloud).
3. **Write pattern** — mostly static/batch-loaded (FAISS is fine, even though it has
   weaker update/delete support) vs. frequent inserts/updates/deletes (Chroma, Qdrant,
   pgvector handle this far better).
4. **Filtering needs** — simple or none (any store) vs. rich metadata filtering combined
   with vector search (Qdrant, pgvector, Pinecone are strongest here).
5. **Existing infrastructure** — already running Postgres? `pgvector` avoids adding a
   new system entirely. Already on a specific cloud? Their managed vector offering may
   be the path of least resistance.

| Store | Best fit | Ops | Notes |
|---|---|---|---|
| Chroma | prototyping, small-medium apps | none (embedded) | easiest to start with |
| FAISS | static/batch datasets, research | none (embedded) | weakest update/delete support |
| Qdrant | production, rich filtering | self-host or managed | strong hybrid search support |
| Pinecone | production, zero-ops | fully managed | usage-based pricing |
| pgvector | teams already on Postgres | whatever you already run | one less system to operate |

**Default recommendation for this course:** start with Chroma (Phase 3–4 default),
move to Qdrant or pgvector when a real deployment need shows up (Phase 10).

## Minimal code

`code.py` implements the five-question decision framework as a small scoring function —
answer the same five questions Topic 07 poses as arguments, get a ranked recommendation
printed out. No API key needed; this topic is pure decision logic.

## Production notes

Re-evaluate this choice once, not continuously — vector store migrations are cheap
*technically* (Topic 06) but not free, so pick based on your 6–12 month outlook, not
today's exact document count.

## Debugging

If two stores score identically in the framework, that's a signal the decision genuinely
doesn't matter much for your case — default to whichever has less operational overhead
for your team.

## Mini challenge

Run the framework twice with different answers modeling "early-stage prototype" and
"planned production system with 10M+ documents" and confirm the recommendations differ
sensibly.
