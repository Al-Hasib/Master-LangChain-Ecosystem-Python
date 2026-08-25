# 05 — Subagents & Delegation

## Problem

Some sub-tasks are noisy by nature — five search queries before finding a good source, a
long back-and-forth verifying one fact — and none of that noise is useful to the main
conversation once the sub-task is done. Doing it inline pollutes the main agent's context
with work that isn't the point.

## Concept

Deep Agents binds a `task` tool **by default** (confirmed via
[docs.langchain.com/oss/python/deepagents/overview](https://docs.langchain.com/oss/python/deepagents/overview)
and
[.../deepagents/subagents](https://docs.langchain.com/oss/python/deepagents/subagents)):
calling it spawns a fresh, isolated agent that runs autonomously and returns **one final
report** — none of its intermediate tool calls or messages join the main conversation.
Even with zero configuration, the main agent already has access to a default
`"general-purpose"` subagent (same instructions, same tools as the parent) purely for
context isolation.

You get *focused* subagents by passing `subagents=` — a list of dicts, each with a
`name`, `description` (how the main agent decides when to delegate to it), and
`system_prompt` (subagents do **not** inherit the parent's system prompt), plus optional
`tools=` (overrides the inherited tool set entirely) and `model=`:

```python
agent = create_deep_agent(
    model=model,
    subagents=[
        {
            "name": "fact-checker",
            "description": "Verifies a single factual claim against the given tools.",
            "system_prompt": "You check ONE claim and report true/false + why.",
            "tools": [lookup_fact],
        },
    ],
)
```

The main agent delegates by calling `task(subagent="fact-checker", ...)` — from the main
conversation's point of view, that's a single tool call in, a single result out.

```text
main agent
    │
    │  task(subagent="fact-checker", input="...")
    ▼
┌───────────────────────────────┐
│ fact-checker (isolated ctx)   │   <- own messages, own tool calls, own noise
│  tool call → tool call → ...  │
└───────────────────────────────┘
    │
    │  ONE final report
    ▼
main agent (context stays clean)
```

## Minimal code

`code.py` configures one focused subagent (`fact-checker`) alongside the default
general-purpose one, asks the main agent a question that should trigger delegation, and
prints the main conversation's message count to make the point that the subagent's
internal back-and-forth never shows up there.

## Production notes

Give each subagent a narrow `description` — that's the only signal the main agent uses to
decide *when* to delegate to it, so a vague description gets it picked (or skipped)
incorrectly. Override `tools=` per subagent so a "fact-checker" can't accidentally call a
tool meant for a different subagent.

## Debugging

If the main agent never delegates, tighten the subagent's `description` to name the
specific situation it should be used for — the main agent is choosing whether to call
`task(...)` the same way it chooses any other tool: from the description alone.

## Mini challenge

Add a second subagent with an overlapping description to one already defined and see
whether the main agent picks the right one consistently — same lesson as Phase 1 Topic
05's overlapping-tools challenge, one level up.
