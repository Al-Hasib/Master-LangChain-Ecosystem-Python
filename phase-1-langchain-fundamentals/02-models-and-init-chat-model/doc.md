# 02 — Models & `init_chat_model`

## Problem

Provider SDKs (Phase 0) are shaped differently enough (parameter names, response
objects) that switching providers means rewriting call sites. Teams frequently need to:
swap models for cost/latency reasons, run the same app against two providers for
comparison, or fall back to a second provider on outage.

## Concept

`init_chat_model` returns the **same object type** (`BaseChatModel`) no matter which
provider string you give it — every downstream call (`.invoke`, `.stream`,
`.bind_tools`, `.with_structured_output`) works identically regardless of provider.

```python
from langchain.chat_models import init_chat_model

openai_model    = init_chat_model("gpt-4o-mini", model_provider="openai")
anthropic_model = init_chat_model("claude-sonnet-4-6", model_provider="anthropic")
# both support the exact same .invoke(), .stream(), .bind_tools(), ... surface
```

Common constructor parameters (all standardized across providers by LangChain):
`temperature`, `max_tokens`, `timeout`, `model_kwargs` (provider-specific escape hatch).

This is the concrete mechanism behind Phase 2's "swap providers without rewriting your
app" — because your application code only ever talks to `BaseChatModel`, not to
`openai.OpenAI` or `anthropic.Anthropic` directly.

## Minimal code

`code.py` initializes both an OpenAI and (if the key is present) an Anthropic model,
sends the identical prompt to each through the identical `.invoke()` call, and prints
both — proving the call site never needed to know which provider it's talking to.

## Production notes

Pin exact model version strings in production (e.g. a dated model id) rather than a
"latest" alias, so behavior doesn't shift under you on a provider-side update. Keep
provider selection in config (env var), not hardcoded, so switching is a config change.

## Debugging

- `model_provider` mismatch with the model name → LangChain raises immediately at
  `init_chat_model` time, not at `.invoke()` time; read the error, it names the issue.
- Missing provider package (e.g. `langchain-anthropic` not installed) → clear
  `ImportError` naming the missing package.

## Mini challenge

Time both providers' response to the same prompt (wall-clock, not token count) and print
which was faster.
