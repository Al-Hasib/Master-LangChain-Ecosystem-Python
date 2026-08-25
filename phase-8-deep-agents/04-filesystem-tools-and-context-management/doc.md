# 04 — Filesystem Tools & Context Management

## Problem

Long research tasks produce a lot of intermediate material — full search results, draft
notes, partial calculations — that the model needs *at some point* but not necessarily in
full, every single turn. Stuffing all of it into the message list bloats context, raises
cost, and makes it easy for the model to lose the actually-important instruction in a sea
of stale intermediate text.

## Concept

Deep Agents binds filesystem tools **by default** (confirmed via
[docs.langchain.com/oss/python/deepagents/middleware](https://docs.langchain.com/oss/python/deepagents/middleware)):
`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `delete`. These operate on a
**virtual filesystem that lives in the LangGraph state** (the docs' own words: *"By
default, these tools write to a local 'filesystem' in your graph state"*) — not your real
disk, and not persisted beyond the run unless you configure a real backend (`backend=`
param, out of scope here). After `agent.invoke(...)`, the returned state dict has a
`"files"` key you can inspect directly, same as `"todos"` in Topic 03.

The pattern this enables: instead of returning a full raw web page as a tool result (and
paying for the model to re-read it every subsequent turn), a tool — or the model itself —
writes the material to a file, and the model reads it back only when it actually needs
that content again.

```text
tool result: 4,000 words of raw search text
        │
        ▼ (write_file("notes/source_1.md", ...))
   state["files"]["notes/source_1.md"]      <- stored ONCE, off the message list
        │
        ▼ (read_file(...) - only when actually needed again)
   model reads it back on demand
```

## Minimal code

`code.py` gives a deep agent a "raw source" tool whose result the agent is instructed to
save to a file rather than reason over directly, then asks a follow-up in the *same run*
that requires reading that file back — printing `result["files"]` to show the scratch
space content at the end.

## Production notes

This is the mechanism Topic 06's research agent leans on hardest: write findings to
named files as you go (`notes/source_1.md`, `notes/source_2.md`, ...), then have a final
step read all of them back to synthesize a report — much cheaper than keeping every
source's full text live in the conversation the whole time.

## Debugging

If `read_file` returns "file not found," check the exact path string the model used to
`write_file` — the virtual filesystem has no autocomplete/fuzzy matching, a mismatched
path (`note.md` vs `notes.md`) is a dead end, not an error the model can usually recover
from without being told the exact discrepancy.

## Mini challenge

Have the agent `write_file` two separate notes, then use `grep` or `glob` (also default
tools) to find which one contains a specific keyword, without reading both in full.
