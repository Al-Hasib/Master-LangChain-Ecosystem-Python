"""
Phase 2 - Topic 07: Choosing a Vector Database

A small scoring framework over the five questions from doc.md. No API key needed -
this topic is pure decision logic, not a model/vector-store call.

Run:
    python code.py
"""

from dataclasses import dataclass

# Each store scored 0-2 on each dimension: higher is a better fit for that dimension.
STORE_SCORES = {
    "FAISS":    {"scale": 1, "low_ops": 2, "frequent_writes": 0, "rich_filtering": 0},
    "Qdrant":   {"scale": 2, "low_ops": 1, "frequent_writes": 2, "rich_filtering": 2},
    "Pinecone": {"scale": 2, "low_ops": 2, "frequent_writes": 2, "rich_filtering": 2},
    "pgvector": {"scale": 1, "low_ops": 1, "frequent_writes": 2, "rich_filtering": 2},
}


@dataclass
class Requirements:
    large_scale: bool          # millions+ vectors expected
    wants_zero_ops: bool       # no appetite to self-host/manage infra
    frequent_updates: bool     # documents added/changed/removed often
    needs_rich_filtering: bool  # combining metadata filters with vector search


def recommend(requirements: Requirements) -> list[tuple[str, int]]:
    weights = {
        "scale": 2 if requirements.large_scale else 0,
        "low_ops": 2 if requirements.wants_zero_ops else 0,
        "frequent_writes": 2 if requirements.frequent_updates else 0,
        "rich_filtering": 2 if requirements.needs_rich_filtering else 0,
    }
    scored = [
        (store, sum(dims[dim] * weight for dim, weight in weights.items()))
        for store, dims in STORE_SCORES.items()
    ]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)


def print_recommendation(label: str, requirements: Requirements) -> None:
    print(f"\n=== {label} ===")
    print(f"  requirements: {requirements}")
    for store, score in recommend(requirements):
        print(f"  {score:3d}  {store}")


def main() -> None:
    print_recommendation(
        "Early-stage prototype",
        Requirements(
            large_scale=False,
            wants_zero_ops=True,
            frequent_updates=False,
            needs_rich_filtering=False,
        ),
    )
    print_recommendation(
        "Production system, 10M+ documents, multi-tenant filtering",
        Requirements(
            large_scale=True,
            wants_zero_ops=True,
            frequent_updates=True,
            needs_rich_filtering=True,
        ),
    )
    print_recommendation(
        "Team already running Postgres, moderate scale",
        Requirements(
            large_scale=False,
            wants_zero_ops=False,
            frequent_updates=True,
            needs_rich_filtering=True,
        ),
    )


if __name__ == "__main__":
    main()
