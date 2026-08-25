# 04 — Streaming APIs & Async Execution

## Problem

Topic 03's `/chat` endpoint is synchronous and non-streaming: the client waits for the
*entire* agent response before seeing anything, and while one request is generating, a
single-worker server can't make progress on another. Neither is acceptable for a chat
product — users expect tokens to appear as they generate (Phase 1 Topic 09's
`model.stream()`), and the server needs to serve concurrent users without a thread per
request.

## Concept

Two upgrades, and they're independent of each other:

- **Streaming over HTTP** — reuse Phase 1 Topic 09's `model.stream()`, but instead of
  `print()`-ing each chunk, `yield` it from a generator that FastAPI's
  `StreamingResponse` sends to the client as the tokens arrive:

```python
from fastapi.responses import StreamingResponse

def token_generator(prompt: str):
    for chunk in model.stream(prompt):
        yield chunk.text

@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    return StreamingResponse(token_generator(request.message), media_type="text/plain")
```

- **Async execution** — swap `def` route handlers for `async def`, and `.invoke()` /
  `.stream()` for `.ainvoke()` / `.astream()`. LangChain agents built on LangGraph
  (`create_agent`, as used throughout this course) support the full async surface —
  `agent.ainvoke(...)` and `agent.astream(...)` exist on the compiled graph they
  return, mirroring their sync counterparts. Async matters for *throughput*: while one
  request awaits the model API over the network, the event loop serves other requests
  instead of sitting idle on a blocked thread.

```text
sync route,  N concurrent requests  -> N threads, each blocked on network I/O
async route, N concurrent requests  -> 1 event loop, all N awaiting concurrently
```

Streaming and async solve different problems and combine freely: an `async def` route
can return a `StreamingResponse` built from an `async def` generator that calls
`await model.astream(...)` internally.

## Minimal code

`code.py` adds two endpoints to Topic 03's app: `POST /chat/stream` (token-by-token
`StreamingResponse` built on `model.stream()`) and `POST /chat/async` (`async def` route
calling `await agent.ainvoke(...)`) — plus a `main()` timing comparison showing
time-to-first-byte for the streaming endpoint's generator vs. a full non-streaming call.

## Production notes

For a chat product, always stream — perceived latency dominates user experience more
than total completion time (Phase 1 Topic 09 measured this directly). For any endpoint
under real concurrent load, prefer `async def` routes with `.ainvoke()`/`.astream()`
over sync ones; FastAPI runs sync `def` routes in a thread pool automatically, which
works but caps concurrency at pool size. This is the layer that makes the Phase project
(Production RAG Architecture) responsive under multiple simultaneous users.

## Debugging

- `StreamingResponse` sends the whole response at once anyway → check you're not
  accidentally materializing the generator into a `list`/`str` before passing it in,
  and that no reverse proxy in front of it (nginx, etc.) is buffering the response.
- `RuntimeError: This event loop is already running` → don't call `asyncio.run()` inside
  an already-async context (e.g. inside a FastAPI async route); just `await` directly.
- Async route feels no faster than sync → confirm you're actually calling `.ainvoke()`/
  `.astream()`, not `.invoke()`/`.stream()` inside an `async def` (that still blocks the
  event loop for the call's duration).

## Mini challenge

Change `/chat/stream` to stream Server-Sent Events (`media_type="text/event-stream"`,
each chunk prefixed `data: `) instead of raw text, and note what a frontend needs to
change to consume it (an `EventSource` instead of reading a raw stream).
