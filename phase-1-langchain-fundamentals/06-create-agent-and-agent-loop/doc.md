# 06 — `create_agent` & the Agent Loop

## Problem

Topic 05 still executed one round of tool calls by hand. Real questions often need
*several* rounds (call a tool, look at the result, decide to call another tool, ...)
before answering. Writing that loop yourself (Phase 0 Topic 01 sketched why) is exactly
the repetitive plumbing LangChain automates.

## Concept

`create_agent` builds a ready-to-run agent: give it a model, a list of tools, and
(optionally) a system prompt — it runs the request → execute → feed-back loop from
Phase 0 Topic 04 automatically, for as many rounds as needed, until the model produces a
final answer with no more tool calls.

```python
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-4o-mini",
    tools=[get_weather],
    system_prompt="You are a helpful assistant.",
)

result = agent.invoke({"messages": [{"role": "user", "content": "Weather in Dhaka?"}]})
print(result["messages"][-1].content)
```

`agent.invoke(...)` takes a dict with a `"messages"` key (a full conversation, like
Phase 0/Topic 03) and returns a dict with the **entire updated message list** — every
tool call and tool result that happened along the way is in there, not hidden.

```text
invoke({"messages":[...]})
        │
        ▼
   ┌─────────────────────────────┐
   │  loop:                      │
   │   model call                │
   │   tool call requested? ──── │──yes──> run tool(s) ──> back to model call
   │   no  ──> done               │
   └─────────────────────────────┘
        │
        ▼
   {"messages": [...original..., AIMessage, ToolMessage, ..., final AIMessage]}
```

This is `create_agent` running **the exact loop Phase 0 Topic 01 sketched by hand** —
underneath, it's built on LangGraph (Phase 6), which is why you'll later be able to drop
down to LangGraph directly for more control.

## Minimal code

`code.py` builds an agent with two tools (`add`, `get_weather`) and asks a question that
requires calling both in sequence, printing every message in the returned list so the
full loop is visible — no manual tool-call handling required, unlike Topic 05.

## Production notes

Always inspect `result["messages"]`, not just the last message, when debugging — it's a
full trace of what the agent decided to do, which is your first debugging tool before
reaching for LangSmith (Phase 9).

## Debugging

- Agent loops without stopping / hits a max-iteration error → usually a tool that never
  produces output the model considers "done," or a system prompt that doesn't tell it
  when to stop.
- Final answer ignores a tool's result → check the tool actually returned useful
  content (an empty string or generic error message gives the model nothing to work
  with).

## Mini challenge

Give the agent three tools where two have overlapping purposes (like Topic 05's
challenge) and see whether it still reaches a correct final answer despite occasional
wrong tool choices mid-loop.
