# 06 — Long-Running Tasks & Deep Research Agents

## Problem

A genuinely long-running task — "research three options, take notes as you go, then
write a comparison" — needs everything the previous four topics introduced working
together: a plan that survives many turns, scratch space so intermediate findings don't
bloat context, and delegation for the noisiest sub-steps. Using only one of the three
still leaves a gap.

## Concept

This topic builds this phase's project, scoped down to what's realistically demonstrable
with free, no-extra-infra tools (DuckDuckGo web search, the built-in virtual filesystem,
one subagent) rather than every capability in the phase README's full diagram:

```text
User → Deep Agent → Planner (write_todos)
         ├── Research Subagent   (delegated via task)
         ├── Web Search          (DuckDuckGo, Phase 1 Topic 11 pattern)
         └── Filesystem notes    (write_file / read_file - Topic 04)
              ↓
        Context Management  (findings saved to files, not kept live in messages)
              ↓
         Final Report
```

Scoping decisions (this is intentionally a subset of the README's 5-box diagram — "Data
Analysis" and "Fact Checking" as separate boxes are left as an extension, since Topic 05
already demonstrated the delegation mechanics they'd use):

- **Web Search** = DuckDuckGo, reusing the exact tool from Phase 1 Topic 11 — no new API
  key needed, matches this repo's "runs for every viewer out of the box" rule.
- **Research Subagent** = one subagent that does search + note-writing for a single
  topic, so the main agent can research multiple topics without each one's search noise
  entering the main conversation.
- **Planner** = `TodoListMiddleware` (Topic 03), so the run's plan is inspectable via
  `result["todos"]`.
- **Context Management** = every subagent-produced note is written to a file (Topic 04)
  and only read back at the final synthesis step.

## Minimal code

`code.py` wires all four pieces into one `create_deep_agent` call and runs it against a
"research N things and compare them" prompt, printing the todo list, the files written,
and the final report — the smallest end-to-end version of the phase project.

## Production notes

A real deep research agent would add retries around web search (Phase 1's fallback
patterns apply unchanged — Deep Agents doesn't replace that), a hard cap on subagent
recursion depth, and LangSmith tracing (Phase 9) to debug *why* a given run took the path
it did — none of which changes the wiring shown here.

## Debugging

If the final report is thin despite multiple searches happening, check `result["files"]`
first — the notes may have been written correctly but never read back at synthesis time,
which is a prompting problem (tell the model explicitly to read its notes before writing
the final report), not a tool problem.

## Mini challenge

Extend `code.py`'s subagent list with a second, differently-focused subagent (e.g. a
"summarizer" that only condenses an already-written file) and have the main agent chain
research → summarize for one topic.
