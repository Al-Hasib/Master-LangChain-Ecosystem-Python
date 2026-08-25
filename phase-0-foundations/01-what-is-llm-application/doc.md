# 01 — What is an LLM Application? (LLM vs Chat Model vs AI Agent)

## Problem

"AI app" gets used for three very different things: a raw text completion, a
back-and-forth chat, and something that takes actions on your behalf. Viewers need
these three terms nailed down before any framework talk makes sense.

## Concept

- **LLM (completion model):** text in → text continuation out. No inherent notion of
  "turns" or roles. Mostly legacy today (e.g. old `text-davinci-*` style APIs).
- **Chat Model:** a model trained/served for structured *conversation turns*
  (`system`/`user`/`assistant` messages). Almost every model you'll use in this course
  is exposed as a chat model, even for single-shot tasks.
- **AI Agent:** a chat model wrapped in a **loop** that can call tools, observe the
  results, and decide what to do next — until it decides the task is done. The
  difference from a chat model isn't the model, it's the control flow around it.

```text
LLM            :  text ---------------------------> text
Chat Model     :  [system, user, assistant, ...] --> assistant message
Agent          :  [messages] -> model -> tool call? -> run tool -> back to model -> ... -> final answer
```

An "LLM application" is any software where a call like these sits in the request path.
Everything in this course is one of: a single chat-model call, a fixed pipeline of
calls (a "chain"), or an agent loop.

## Minimal code

`code.py` calls the same provider three conceptual ways: a bare completion-style prompt,
a proper multi-turn chat, and a stubbed-out "one loop iteration" of tool decision-making
— without any agent framework, so you can see exactly what a framework will later
automate for you.

## Production notes

Production apps almost never use a raw completion model anymore — start every mental
model from "chat model," and treat "agent" as "chat model + loop + tools," not as a
separate kind of model.

## Debugging

- If output looks like it's continuing your prompt instead of answering it, you're
  likely using a completion-style prompt format with a chat model — fix your message
  roles.
- "The agent didn't call my tool" is almost always a system-prompt/tool-description
  problem, not a model capability problem — covered in Phase 1's tools topic.

## Mini challenge

Modify `code.py` to ask the same question three times with different `system` messages
(helpful assistant / terse assistant / assistant that answers only in bullet points) and
compare outputs.
