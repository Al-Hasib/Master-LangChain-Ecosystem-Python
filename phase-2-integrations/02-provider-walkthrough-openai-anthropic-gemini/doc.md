# 02 — Provider Walkthrough: OpenAI, Anthropic, Gemini

## Problem

Topic 01 proved the *interface* is identical across providers. It doesn't tell you
*which* provider to reach for. Viewers need concrete tradeoffs, not just "they're all
the same" — because they aren't, once you look past `.invoke()`.

## Concept

All three are reached through `init_chat_model`, differing only in the provider string
and package installed (`langchain-openai`, `langchain-anthropic`,
`langchain-google-genai`):

| | OpenAI | Anthropic | Gemini |
|---|---|---|---|
| Package | `langchain-openai` | `langchain-anthropic` | `langchain-google-genai` |
| Provider string | `"openai"` | `"anthropic"` | `"google_genai"` |
| Strength | broad tool ecosystem, fast small models | strong reasoning/instruction-following, large context | strong multimodal (native image/video/audio), competitive pricing |
| Typical fit | general-purpose default, high tool-call reliability | complex reasoning tasks, long documents | multimodal apps, cost-sensitive large-context tasks |

Practical differences that *do* leak through the standard interface:
- **Auth env var name** differs per provider (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
  `GOOGLE_API_KEY`) — `init_chat_model` reads the right one automatically based on
  `model_provider`.
- **Rate limits, context window size, and pricing** differ meaningfully and should
  drive the choice for a given workload, not brand preference.
- **Streaming and tool-calling support** are all present across the three, but subtle
  differences (e.g. how parallel tool calls are handled) can surface in edge cases —
  covered as they come up in later phases.

## Minimal code

`code.py` sends the identical prompt to all three providers (skipping any without a key
set) and prints response + latency side by side, so the comparison is concrete rather
than just asserted.

## Production notes

Many production systems use **more than one provider** deliberately: a fast/cheap model
for simple classification steps, a stronger model for complex reasoning steps, with
`with_fallbacks` (Phase 1 Topic 08) providing resilience if either has an outage.

## Debugging

- `AuthenticationError` naming a provider you didn't intend to call → check you didn't
  typo `model_provider` (e.g. `"google"` instead of `"google_genai"`).
- Response quality differs a lot between providers on the *same* prompt → prompts
  aren't fully portable; expect to tune wording slightly per provider for best results.

## Mini challenge

Run a reasoning-heavy prompt (e.g. a multi-step logic puzzle) against all three and
compare not just the answer but how each explains its reasoning.
