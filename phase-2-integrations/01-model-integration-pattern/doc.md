# 01 — Model Integration Pattern

## Problem

Phase 1 Topic 02 showed `init_chat_model` returning the same object type for OpenAI and
Anthropic. This topic makes the point sharper: **your application code should never
import a provider-specific class directly** — if it does, every downstream function
that touches the model is now coupled to that provider.

## Concept

The pattern in one sentence: **write functions against `BaseChatModel`, construct the
concrete model once at the edge of your app (config), and never let a provider-specific
type leak past that boundary.**

```python
from langchain_core.language_models import BaseChatModel

def summarize(model: BaseChatModel, text: str) -> str:
    """Doesn't know or care which provider `model` came from."""
    return model.invoke(f"Summarize in one sentence: {text}").content
```

`summarize` above works unchanged whether `model` was built with
`init_chat_model("gpt-4o-mini", model_provider="openai")`,
`init_chat_model("claude-sonnet-4-6", model_provider="anthropic")`, or any other
provider covered in Topics 02–03. The construction call is the *only* place in your
codebase that names a provider — ideally driven by a config value (env var), not a
hardcoded string, so switching providers is a deploy-config change, not a code change.

```text
config (env var: MODEL_PROVIDER=openai)
        │
        ▼
init_chat_model(...)   <-- the ONLY place a provider name appears
        │
        ▼
BaseChatModel  ─────────────────────────►  every function downstream
```

## Minimal code

`code.py` defines one function (`summarize`) that only knows about `BaseChatModel`, then
calls it with models built from two different providers (skipping Anthropic gracefully
if no key is set) — proving zero code duplication is needed per provider.

## Production notes

Keep provider selection in `config.py` (Phase 1 Topic 10's pattern), read from an
environment variable. This is also what makes fallback chains (Phase 1 Topic 08,
`with_fallbacks`) practical — the fallback model is constructed the same way as the
primary.

## Debugging

If you find yourself writing `if provider == "openai": ... elif provider == "anthropic":
...` branches anywhere outside your model-construction code, that's a sign the pattern
has leaked — refactor back to constructing once and passing a `BaseChatModel` around.

## Mini challenge

Add a third branch for a provider you haven't set up credentials for, and confirm the
`summarize` function still doesn't need to change — only the construction call does.
