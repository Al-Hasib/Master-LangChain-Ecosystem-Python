# 03 — Local & Alternative Providers (Ollama, OpenRouter)

## Problem

Every provider so far is a paid, hosted API. Two real needs aren't covered by that:
running models **locally** (privacy, zero marginal cost, offline dev) and reaching many
providers through **one routing layer** without juggling separate SDKs/keys.

## Concept

**Ollama** — runs open models (Llama, Mistral, Gemma, ...) on your own machine via a
local server (`http://localhost:11434`). Reached the same way as any other provider:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("llama3.1", model_provider="ollama")
```

Requires the Ollama app running locally and the model already pulled (`ollama pull
llama3.1`) — this is the one provider in the course that isn't "just an API key," and
`code.py` handles the connection-refused case gracefully if it isn't running.

**OpenRouter** — an OpenAI-compatible routing API that proxies to dozens of providers
(OpenAI, Anthropic, Meta, Mistral, and more) behind one key and one bill. Because it's
OpenAI-*compatible*, you reach it with `ChatOpenAI` pointed at a different `base_url`
rather than through `init_chat_model`'s provider table:

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    model="meta-llama/llama-3.1-8b-instruct",
)
```

**When to reach for which:**
| Need | Use |
|---|---|
| Data must never leave your machine | Ollama |
| Fast, free local dev/testing loop | Ollama |
| Access many providers/models without separate integrations | OpenRouter |
| Compare models across vendors quickly | OpenRouter |
| Lowest latency / provider-specific features | Direct provider SDK (Topic 02) |

## Minimal code

`code.py` tries Ollama first (catching the "server not running" case with a clear
message instead of a stack trace) and OpenRouter second (skipped if no key is set),
using the exact same downstream pattern from Topic 01 either way.

## Production notes

Ollama in production usually means self-hosting the inference server yourself (not just
a laptop) — treat it as an infrastructure decision, not just a code change. OpenRouter
adds a small latency/cost overhead versus calling a provider directly, in exchange for
flexibility — fine for prototyping, worth re-evaluating for high-volume production paths.

## Debugging

- `ConnectionError` from Ollama → the Ollama app isn't running, or the model wasn't
  pulled yet (`ollama pull <model>`).
- OpenRouter returns a model-not-found error → model identifiers on OpenRouter are
  namespaced (`provider/model-name`) and differ from the provider's own naming.

## Mini challenge

If you have Ollama installed, pull two different local models and compare their
tool-calling reliability against the tool-calling demo from Phase 1 Topic 05.
