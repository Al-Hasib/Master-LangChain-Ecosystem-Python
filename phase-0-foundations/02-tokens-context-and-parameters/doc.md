# 02 — Tokens, Context Windows & Model Parameters

## Problem

Viewers hit two walls immediately: "why did my long document get truncated / cost so
much?" and "why does the model answer differently every time I run it?" Both are
answered by tokens, context windows, and sampling parameters.

## Concept

- **Tokens** are the model's unit of text — roughly 4 characters / ¾ of a word in
  English. Pricing and limits are all counted in tokens, not characters or words.
- **Context window** is the max tokens (input + output combined) a model can attend to
  in one call. Exceeding it truncates or errors — this is *the* constraint that drives
  chunking (Phase 3) and context management (Phase 7–8).
- **Key sampling parameters:**
  - `temperature` — randomness. `0` = near-deterministic, `1+` = more varied/creative.
  - `top_p` — nucleus sampling; alternative/complementary randomness control.
  - `max_tokens` — hard cap on the *output* length (does not affect input).
- Rule of thumb: use low temperature for extraction/classification/structured output,
  higher temperature for brainstorming/creative tasks.

## Minimal code

`code.py` counts tokens for a piece of text with `tiktoken`, shows how token count
diverges from word count, and runs the same prompt at `temperature=0` vs `temperature=1`
twice each so you can see the determinism difference directly.

## Production notes

Always budget tokens explicitly: input tokens (system + history + retrieved context) +
`max_tokens` for output must stay under the model's context window, with headroom. This
becomes critical once RAG (Phase 3) starts stuffing retrieved chunks into the prompt.

## Debugging

- "Response got cut off mid-sentence" → `max_tokens` too low, raise it.
- "Getting a context-length-exceeded error" → your input (often accumulated chat
  history) exceeds the window; you need trimming/summarization (Phase 7).
- "Same prompt, different answer every time, and I need consistency" → set
  `temperature=0` (note: still not perfectly deterministic across all providers).

## Mini challenge

Count tokens for three prompts of increasing length and compute the approximate cost
using a provider's published per-token pricing.
