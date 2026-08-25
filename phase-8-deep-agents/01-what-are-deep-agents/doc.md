# 01 — What are Deep Agents?

## Problem

Phase 1's `create_agent` (Topic 06) runs the request → tool-call → feed-back loop
automatically, which is a huge upgrade over hand-rolled loops — but it only manages *one*
resource: the message list. For a short task (1-3 tool calls) that's plenty. For a
long-horizon task — "research these five things, cross-check them, and write a report" —
three problems show up fast:

- **No persistent plan.** The model has to keep re-deriving "what have I done, what's
  left" from the raw message history every turn. Long histories make this unreliable.
- **Context bloat.** Every intermediate result (a full web page, a draft paragraph, a
  large tool output) gets stuffed into the same message list the model re-reads on every
  turn — burning tokens and diluting attention on what actually matters *now*.
- **No isolation.** A messy sub-investigation (five failed search queries before finding
  the right source) permanently pollutes the main conversation; there's no way to hand
  off a self-contained chunk of work and get back just the answer.

## Concept

**Deep Agents is a harness, not a replacement.** `create_deep_agent` (package:
`deepagents`, confirmed at
[docs.langchain.com/oss/python/deepagents/quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart))
returns a compiled LangGraph state graph — the exact same kind of object `create_agent`
returns, invoked the exact same way:

```python
from deepagents import create_deep_agent

agent = create_deep_agent(model=model, tools=[my_tool], system_prompt="...")
result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

What it adds on top, built in and bound automatically (confirmed via
[docs.langchain.com/oss/python/deepagents/overview](https://docs.langchain.com/oss/python/deepagents/overview)
and
[.../deepagents/middleware](https://docs.langchain.com/oss/python/deepagents/middleware)):

| Add-on | Default? | What it solves |
|---|---|---|
| Filesystem tools (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `delete`) | **on** | Scratch space that lives in graph state, not the message list (Topic 04) |
| `task` tool (subagent delegation, default "general-purpose" subagent) | **on** | Isolate noisy sub-work, return just the result (Topic 05) |
| `write_todos` (via `TodoListMiddleware`) | **opt-in** | Explicit, model-editable plan (Topic 03) |

```text
create_agent:      [ model ] <--> [ tools ]   (loop over ONE message list)

create_deep_agent: [ model ] <--> [ tools ]   (same loop, PLUS:)
                        │
                        ├── virtual filesystem  (state["files"])
                        ├── task tool           (spawn isolated subagents)
                        └── write_todos (opt-in) (state["todos"])
```

Everything from Phase 1 (tools built with `@tool`, models via `init_chat_model`) still
applies unchanged — Deep Agents sits *on top of* that layer, it doesn't replace it.

## Minimal code

`code.py` runs the same small question through a plain `create_agent` first (Phase 1
baseline — note there's nowhere for intermediate state to live but the message list),
then through `create_deep_agent` with the exact same `tools=` list and no other config,
and shows the deep agent's result already carries a `"files"` key in its returned state —
proof the scratch space exists even when unused.

## Production notes

Reach for Deep Agents when a task is genuinely long-horizon (multiple research/write/
verify phases, likely to run for minutes not seconds). For anything a 2-3 tool-call
`create_agent` handles comfortably, adding the harness is pure overhead — see Topic 08.

## Debugging

If `create_deep_agent` result messages look identical to `create_agent`'s for a given
task, that's not a bug — it means the task didn't need the extra machinery. The harness
only pays off once the model actually reaches for filesystem/task/todo tools.

## Mini challenge

Rerun `code.py`'s question but make it deliberately multi-phase ("research three note-
taking apps' pricing, write a comparison table, then a one-line recommendation") and
check whether the deep agent starts writing to `files` unprompted.
