"""
Phase 10 - Topic 07: Auth, Rate Limiting & Caching

A FastAPI API-key auth dependency, a stdlib in-memory token-bucket rate limiter, and
a simple prompt-hash response cache - all runnable without external infra. Production
upgrade path (Redis-backed, shared across instances) is Topic 06.

Run:
    uvicorn code:app --reload
    python code.py                 # runs a rate-limit demo, then serves the app
"""

import hashlib
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

try:
    from fastapi import Depends, FastAPI, Header, HTTPException
    from pydantic import BaseModel, Field
except ImportError:
    sys.exit(
        "Missing dependency. Run: pip install -r ../../requirements.txt\n"
        "(fastapi/uvicorn are commented out in requirements.txt for Phase 10 - "
        "uncomment them, or: pip install fastapi uvicorn)"
    )


# ============================================================================
# 1) Auth - a FastAPI dependency. Runs before the route body; an invalid key
# never reaches the (expensive) model call.
# ============================================================================
VALID_API_KEYS = {"demo-key-123"}  # in production: looked up from a DB/secrets store


def require_api_key(x_api_key: str = Header(default="")) -> str:
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key header")
    return x_api_key


# ============================================================================
# 2) Rate limiting - token bucket, in-memory, per API key. Correct for a
# single process; Topic 06's Redis is the multi-instance-safe upgrade.
# ============================================================================
class TokenBucket:
    def __init__(self, capacity: int = 5, refill_per_second: float = 1.0):
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._tokens: dict[str, float] = {}
        self._last_refill: dict[str, float] = {}

    def _refill(self, key: str) -> None:
        now = time.monotonic()
        last = self._last_refill.get(key, now)
        elapsed = now - last
        current = self._tokens.get(key, self.capacity)
        self._tokens[key] = min(self.capacity, current + elapsed * self.refill_per_second)
        self._last_refill[key] = now

    def allow(self, key: str) -> bool:
        self._refill(key)
        if self._tokens[key] >= 1:
            self._tokens[key] -= 1
            return True
        return False


_rate_limiter = TokenBucket(capacity=5, refill_per_second=1.0)


def enforce_rate_limit(api_key: str = Depends(require_api_key)) -> str:
    if not _rate_limiter.allow(api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded - try again shortly")
    return api_key


# ============================================================================
# 3) Caching - dict keyed by a hash of the prompt, with a TTL. A plain dict
# works here (rather than functools.lru_cache) because the cache key needs to
# be derived from a normalized/hashed prompt string, not a function's args.
# ============================================================================
class PromptCache:
    def __init__(self, ttl_seconds: float = 300.0):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, str]] = {}

    @staticmethod
    def _key(prompt: str, model_name: str) -> str:
        # Model name is part of the key - a cached answer from one config
        # must never be served for a different one.
        return hashlib.sha256(f"{model_name}:{prompt}".encode()).hexdigest()

    def get(self, prompt: str, model_name: str) -> str | None:
        key = self._key(prompt, model_name)
        entry = self._store.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if time.time() - stored_at > self.ttl_seconds:
            del self._store[key]
            return None
        return value

    def set(self, prompt: str, model_name: str, value: str) -> None:
        self._store[self._key(prompt, model_name)] = (time.time(), value)


_cache = PromptCache(ttl_seconds=300.0)
MODEL_NAME = "gpt-4o-mini"


# ============================================================================
# Wired together: auth -> rate limit -> cache -> model call, in that order.
# ============================================================================
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    cached: bool


app = FastAPI(title="Phase 10 Topic 07 - Auth, Rate Limiting & Caching")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, api_key: str = Depends(enforce_rate_limit)) -> ChatResponse:
    cached = _cache.get(request.message, MODEL_NAME)
    if cached is not None:
        return ChatResponse(reply=cached, cached=True)

    if not os.getenv("OPENAI_API_KEY"):
        reply = "(stub - set OPENAI_API_KEY to call the real model)"
    else:
        from langchain.chat_models import init_chat_model

        model = init_chat_model(MODEL_NAME, model_provider="openai", temperature=0)
        reply = model.invoke(request.message).content

    _cache.set(request.message, MODEL_NAME, reply)
    return ChatResponse(reply=reply, cached=False)


def demo_rate_limiter() -> None:
    print("=== Token bucket rate limiter demo (capacity=3, refill=0/s for the demo) ===")
    bucket = TokenBucket(capacity=3, refill_per_second=0.0)
    for i in range(5):
        allowed = bucket.allow("demo-caller")
        print(f"  request {i + 1}: {'allowed' if allowed else 'BLOCKED (429)'}")


def main() -> None:
    demo_rate_limiter()

    try:
        import uvicorn
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    print("\nStarting API at http://127.0.0.1:8000")
    print('Try: curl -X POST http://127.0.0.1:8000/chat -H "X-API-Key: demo-key-123" '
          '-H "Content-Type: application/json" -d "{\\"message\\": \\"Hi\\"}"')
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
