"""
Phase 10 - Topic 08: Cost & Latency Optimization

Runs the same prompts through two configurations (no cache vs. Topic 07's
PromptCache) counting tokens (tiktoken, cost proxy) and wall-clock time
(latency), then prints a side-by-side comparison.

Run:
    python code.py
"""

import hashlib
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gpt-4o-mini"
PROMPTS = [
    "What is the capital of France?",
    "Summarize the benefits of caching in one sentence.",
    "What is the capital of France?",  # repeated on purpose - shows cache payoff
]


# ============================================================================
# Same PromptCache shape as Topic 07 (kept self-contained here so this topic
# runs standalone without importing across topic folders).
# ============================================================================
class PromptCache:
    def __init__(self, ttl_seconds: float = 300.0):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, str]] = {}

    @staticmethod
    def _key(prompt: str, model_name: str) -> str:
        return hashlib.sha256(f"{model_name}:{prompt}".encode()).hexdigest()

    def get(self, prompt: str, model_name: str) -> str | None:
        key = self._key(prompt, model_name)
        entry = self._store.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if time.time() - stored_at > self.ttl_seconds:
            del self._store[key]
            return None
        return value

    def set(self, prompt: str, model_name: str, value: str) -> None:
        self._store[self._key(prompt, model_name)] = (time.time(), value)


def count_tokens(text: str) -> int:
    import tiktoken

    encoding = tiktoken.encoding_for_model(MODEL_NAME)
    return len(encoding.encode(text))


def run_config(prompts: list[str], model, cache: PromptCache | None) -> list[dict]:
    """Runs every prompt through `model`, optionally consulting `cache` first.
    Returns one row of measurements per prompt."""
    rows = []
    for prompt in prompts:
        start = time.perf_counter()
        cached_hit = False

        response_text = cache.get(prompt, MODEL_NAME) if cache else None
        if response_text is not None:
            cached_hit = True
        else:
            response_text = model.invoke(prompt).content
            if cache is not None:
                cache.set(prompt, MODEL_NAME, response_text)

        elapsed = time.perf_counter() - start
        tokens_in = count_tokens(prompt)
        tokens_out = 0 if cached_hit else count_tokens(response_text)

        rows.append(
            {
                "prompt": prompt,
                "cached": cached_hit,
                "elapsed_s": elapsed,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
            }
        )
    return rows


def print_summary(label: str, rows: list[dict]) -> None:
    print(f"\n--- {label} ---")
    total_time = 0.0
    total_tokens = 0
    for row in rows:
        hit = "HIT " if row["cached"] else "MISS"
        print(
            f"  [{hit}] {row['elapsed_s']:.3f}s  "
            f"tokens_in={row['tokens_in']:<4} tokens_out={row['tokens_out']:<4}  "
            f"{row['prompt'][:40]!r}"
        )
        total_time += row["elapsed_s"]
        total_tokens += row["tokens_in"] + row["tokens_out"]
    print(f"  TOTAL: {total_time:.3f}s, {total_tokens} tokens")


def main() -> None:
    try:
        import tiktoken  # noqa: F401
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )

    try:
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    model = init_chat_model(MODEL_NAME, model_provider="openai", temperature=0)

    print("=== Config A: no cache (every prompt hits the model) ===")
    rows_no_cache = run_config(PROMPTS, model, cache=None)
    print_summary("no cache", rows_no_cache)

    print("\n=== Config B: with PromptCache (repeated prompt should hit) ===")
    cache = PromptCache()
    rows_cached = run_config(PROMPTS, model, cache=cache)
    print_summary("with cache", rows_cached)

    time_saved = sum(r["elapsed_s"] for r in rows_no_cache) - sum(
        r["elapsed_s"] for r in rows_cached
    )
    print(
        f"\nCache saved ~{time_saved:.3f}s of wall-clock time across "
        f"{len(PROMPTS)} calls ({sum(1 for r in rows_cached if r['cached'])} cache hit(s))."
    )


if __name__ == "__main__":
    main()
