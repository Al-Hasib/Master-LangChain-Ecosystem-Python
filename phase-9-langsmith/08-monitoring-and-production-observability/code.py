"""
Phase 9 - Topic 08: Monitoring & Production Observability

Computes a local stand-in for what LangSmith's hosted dashboards show in
aggregate: per-call latency (time.perf_counter) and token/cost estimates
(tiktoken) for a handful of calls.

Run:
    python code.py
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

# Approximate, illustrative only - real pricing changes over time and varies by
# model; production cost tracking should come from the provider's actual usage
# response (which is what LangSmith's dashboard uses), not a hardcoded constant.
PRICE_PER_1K_INPUT_TOKENS_USD = 0.00015  # gpt-4o-mini input, approx, snapshot-in-time
PRICE_PER_1K_OUTPUT_TOKENS_USD = 0.00060  # gpt-4o-mini output, approx, snapshot-in-time

PROMPTS = [
    "What is 12 * 7?",
    "Name two benefits of retrieval-augmented generation over a plain chatbot.",
    "In one sentence, explain why observability matters for LLM applications in production.",
]


def require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def main() -> None:
    require_openai_key()
    try:
        import tiktoken
        from langchain.chat_models import init_chat_model
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    tracing_on = (
        os.getenv("LANGCHAIN_API_KEY")
        and os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    )
    if tracing_on:
        print("LangSmith tracing is ON - these same calls are ALSO landing as traces,")
        print("which is what a real dashboard would aggregate over time.\n")
    else:
        print("[note] LangSmith tracing is off - this script still computes the local")
        print("stand-in stats below; set LANGCHAIN_API_KEY + LANGCHAIN_TRACING_V2=true")
        print("in ../../.env to also see these calls as real traces.\n")

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    encoding = tiktoken.encoding_for_model("gpt-4o-mini")

    latencies_s = []
    input_tokens_total = 0
    output_tokens_total = 0

    print("=== Per-call stats (the raw ingredients a dashboard aggregates) ===")
    for prompt in PROMPTS:
        start = time.perf_counter()
        response = model.invoke(prompt)
        elapsed = time.perf_counter() - start

        input_tokens = len(encoding.encode(prompt))
        output_tokens = len(encoding.encode(response.content))
        latencies_s.append(elapsed)
        input_tokens_total += input_tokens
        output_tokens_total += output_tokens

        print(f"  prompt: {prompt[:50]!r}...")
        print(
            f"    latency={elapsed:.2f}s  input_tokens={input_tokens}  "
            f"output_tokens={output_tokens}"
        )

    estimated_cost_usd = (
        input_tokens_total / 1000 * PRICE_PER_1K_INPUT_TOKENS_USD
        + output_tokens_total / 1000 * PRICE_PER_1K_OUTPUT_TOKENS_USD
    )

    print("\n=== Local aggregate (stand-in for a hosted dashboard) ===")
    print(f"Calls made:          {len(PROMPTS)}")
    print(f"Total latency:       {sum(latencies_s):.2f}s")
    print(f"Average latency:     {sum(latencies_s) / len(latencies_s):.2f}s")
    print(f"Total input tokens:  {input_tokens_total}")
    print(f"Total output tokens: {output_tokens_total}")
    print(f"Estimated cost:      ${estimated_cost_usd:.6f} (approximate, snapshot pricing)")

    print(
        "\nWhat this script CANNOT show you, because it's a hosted web-app feature: "
        "p50/p95/p99 latency trends over thousands of runs, cost-over-time charts, "
        "error-rate alerting, and slicing any of this by metadata (user, version, "
        "customer tier). That's what LangSmith's Monitoring tab adds on top of the "
        "same underlying per-run data this script just computed by hand."
    )
    project = os.getenv("LANGCHAIN_PROJECT", "langchain-ecosystem-course")
    print(f"\n  https://smith.langchain.com/  ->  project \"{project}\"  ->  Monitor tab")


if __name__ == "__main__":
    main()
