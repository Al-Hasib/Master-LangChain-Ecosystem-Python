"""
Phase 8 - Topic 08: When NOT to Use Deep Agents

A small, pure-Python decision framework - no API key needed. Same shape as Phase 2
Topic 07's vector-database chooser: answer a few yes/no signals about a task, get a
ranked recommendation of create_agent vs. explicit LangGraph vs. create_deep_agent.

Run:
    python code.py
"""

from dataclasses import dataclass

# Each option scored 0-2 on each dimension: higher is a better fit for that dimension.
OPTION_SCORES = {
    "create_agent (Phase 1)": {
        "short_task": 2, "needs_explicit_control": 0, "long_horizon": 0, "needs_isolation": 0,
    },
    "explicit LangGraph StateGraph (Phase 6)": {
        "short_task": 0, "needs_explicit_control": 2, "long_horizon": 1, "needs_isolation": 0,
    },
    "create_deep_agent (Phase 8)": {
        "short_task": 0, "needs_explicit_control": 0, "long_horizon": 2, "needs_isolation": 2,
    },
}


@dataclass
class TaskProfile:
    finishes_in_few_tool_calls: bool  # 1-3 tool calls total, predictable
    needs_exact_step_control: bool    # you must dictate branching/order yourself
    is_long_horizon: bool             # many phases, unpredictable step count
    has_noisy_sub_work: bool          # sub-steps produce a lot of throwaway context


def recommend(profile: TaskProfile) -> list[tuple[str, int]]:
    weights = {
        "short_task": 2 if profile.finishes_in_few_tool_calls else 0,
        "needs_explicit_control": 2 if profile.needs_exact_step_control else 0,
        "long_horizon": 2 if profile.is_long_horizon else 0,
        "needs_isolation": 2 if profile.has_noisy_sub_work else 0,
    }
    scored = [
        (option, sum(dims[dim] * weight for dim, weight in weights.items()))
        for option, dims in OPTION_SCORES.items()
    ]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)


def print_recommendation(label: str, profile: TaskProfile) -> None:
    print(f"\n=== {label} ===")
    print(f"  profile: {profile}")
    for option, score in recommend(profile):
        print(f"  {score:3d}  {option}")


def main() -> None:
    print_recommendation(
        "Answer 'what's the weather + do this math' (Phase 1 Topic 06 style)",
        TaskProfile(
            finishes_in_few_tool_calls=True,
            needs_exact_step_control=False,
            is_long_horizon=False,
            has_noisy_sub_work=False,
        ),
    )
    print_recommendation(
        "Customer support: classify -> route -> human approval -> respond",
        TaskProfile(
            finishes_in_few_tool_calls=False,
            needs_exact_step_control=True,
            is_long_horizon=False,
            has_noisy_sub_work=False,
        ),
    )
    print_recommendation(
        "Deep research report across many sources with sub-investigations",
        TaskProfile(
            finishes_in_few_tool_calls=False,
            needs_exact_step_control=False,
            is_long_horizon=True,
            has_noisy_sub_work=True,
        ),
    )


if __name__ == "__main__":
    main()
