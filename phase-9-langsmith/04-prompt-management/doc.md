# 04 — Prompt Management

## Problem

Every phase so far has hardcoded prompts as Python strings/f-strings inside `code.py`.
That's fine for a course example, but in a real app it has two problems: (1) changing a
prompt means a code change + redeploy, even though a prompt is really more like content
than logic, and (2) there's no history — you can't easily diff "what did the prompt say
last Tuesday, before the answer quality dropped?"

## Concept

There are two valid ways to manage prompts as they mature, and most teams end up using
both at different stages:

```text
LOCAL VERSION CONTROL                  LANGSMITH PROMPT HUB
(prompts live in your repo)            (prompts live in LangSmith, pulled at runtime)
──────────────────────────             ─────────────────────────────────────────────
+ reviewed in normal PRs                + non-engineers can edit/test prompts
+ no network call to fetch a prompt     + full version history + diffs in the UI
+ works with zero LangSmith setup       + A/B test a prompt change with no deploy
- editing needs a deploy                - adds a network dependency at startup
- no built-in diff/version UI           - needs a LangSmith account
```

**Local version control** is just discipline: keep prompts in a dedicated module (e.g.
`prompts.py`), and put a version comment/changelog above each one, the same way you'd
version a schema. This repo's convention has actually been doing a lightweight version of
this all along — prompts live in `code.py` as clearly-labeled constants.

**Prompt Hub** is LangSmith's hosted alternative: prompts are pushed/pulled through the
SDK, each push creates a new commit with a hash, and `pull_prompt` fetches by name (with
an optional commit/tag) instead of by reading a local file:

```python
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

client = Client()
prompt = ChatPromptTemplate.from_template("Answer concisely: {question}")

# Pushes a new commit under this name (creates the prompt on first push).
url = client.push_prompt("my-course/qa-prompt", object=prompt)

# Pulls the latest commit by name - this is what your app calls at runtime.
pulled = client.pull_prompt("my-course/qa-prompt")
```

`pull_prompt` returns a real `ChatPromptTemplate` (or a full chain if you pushed one with
`include_model=True`) — it slots into the exact same `prompt | model` pipe syntax from
Phase 1, no special handling required downstream.

## Minimal code

`code.py` demonstrates both patterns. It always prints the local-version-control style
(a small `PROMPTS` dict with a version comment per entry) since that needs nothing but
Python. If `LANGCHAIN_API_KEY` is set, it *also* makes real `push_prompt` /
`pull_prompt` calls against your LangSmith workspace, then runs the pulled prompt through
a model — a genuine round trip, not a simulation.

## Production notes

- Namespace prompt names by project (`myapp/summarizer`, not `summarizer`) — Prompt Hub
  names are workspace-wide.
- Pin to a specific commit hash (or a tag like `"prod"`) in production instead of always
  pulling `"latest"` — otherwise someone editing the prompt in the UI changes production
  behavior instantly, with no code review.
- Either pattern benefits from the same discipline: never string-concatenate untrusted
  user input directly into a system prompt (prompt-injection surface) — that's a Phase 10
  topic, but it applies regardless of where the prompt text physically lives.

## Debugging

- `pull_prompt` returns unexpected/stale content → you're pulling `"latest"` and someone
  pushed a change; pin a commit hash to make pulls reproducible.
- `push_prompt` succeeds but the app's behavior doesn't change → the app is still reading
  the old local hardcoded string somewhere and never calls `pull_prompt` at all — a
  half-migration is worse than picking one pattern consistently.

## Mini challenge

Push two different versions of the same prompt name (change the template text, call
`push_prompt` again), then use `client.pull_prompt("name", include_model=False)` with an
explicit commit hash from the first push to confirm you can still retrieve the *old*
version on demand.
