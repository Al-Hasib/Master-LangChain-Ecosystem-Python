# 03 — Messages & Roles (System / User / Assistant)

## Problem

Beginners often dump everything — instructions, examples, and the actual question —
into one blob of text. Understanding message *roles* is what makes prompting reliable
and what LangChain's `Message` objects (Phase 1) are modeling directly.

## Concept

Three roles carry almost all the weight:

- **`system`** — standing instructions for the whole conversation (persona, constraints,
  output format). Sent once, applies to every turn.
- **`user`** — what the human (or, in an agent, the "requester") said.
- **`assistant`** — what the model said previously. Including prior assistant turns is
  what makes a "conversation" instead of independent single-shot calls.

A fourth role, **`tool`**, appears once tool calling is introduced (Topic 04) — it
carries a tool's result back to the model.

```text
[system]     "You are a terse Python tutor. Answer in <=2 sentences."
[user]       "What's a list comprehension?"
[assistant]  "..."
[user]       "Show one for squaring numbers 1-5."
```

Every call to a chat model sends the **entire message list**, not just the newest
message — the model has no memory between API calls. "Conversation memory" is just
your application re-sending the growing message list (Phase 1 covers this properly).

## Minimal code

`code.py` builds a message list turn-by-turn, appending each assistant reply before
adding the next user message, and prints the full list before each call so you can see
exactly what's sent.

## Production notes

The system message is your highest-leverage lever for behavior control — before
reaching for fine-tuning or complex prompting, tighten the system message. Also: message
history grows unbounded unless you manage it (Phase 2/7 cover trimming/summarizing).

## Debugging

- Model ignoring your instructions → check whether they're in `system` (respected more
  strongly) vs buried in a `user` message.
- Model "forgetting" earlier context → you likely aren't resending prior turns.

## Mini challenge

Build a 4-turn conversation where each `user` message refers back to something from two
turns earlier ("the thing I mentioned before") and confirm the model tracks it.
