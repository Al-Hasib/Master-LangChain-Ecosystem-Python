"""
Phase 10 - Topic 04: Streaming APIs & Async Execution

Adds a streaming endpoint (StreamingResponse over model.stream()) and an async
endpoint (async def route + agent.ainvoke()) to Topic 03's FastAPI app.

Run:
    uvicorn code:app --reload
    python code.py                 # also works - runs a local demo + serves the app
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

try:
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ImportError:
    sys.exit(
        "Missing dependency. Run: pip install -r ../../requirements.txt\n"
        "(fastapi/uvicorn are commented out in requirements.txt for Phase 10 - "
        "uncomment them, or: pip install fastapi uvicorn)"
    )


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str


MODEL_NAME = "gpt-4o-mini"
_model = None
_agent = None


def require_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
            "2) fill in your key\n3) re-run"
        )


def get_model():
    global _model
    if _model is None:
        require_api_key()
        from langchain.chat_models import init_chat_model

        _model = init_chat_model(MODEL_NAME, model_provider="openai", temperature=0)
    return _model


def get_agent():
    global _agent
    if _agent is None:
        require_api_key()
        from langchain.agents import create_agent

        _agent = create_agent(model=MODEL_NAME, tools=[], system_prompt="You are a helpful assistant.")
    return _agent


app = FastAPI(title="Phase 10 Topic 04 - Streaming & Async")


@app.get("/health")
def health():
    return {"status": "ok"}


def _token_generator(prompt: str):
    """Plain generator (sync) - StreamingResponse can consume either a sync
    or async generator; sync is enough since model.stream() is itself sync."""
    model = get_model()
    for chunk in model.stream(prompt):
        if chunk.text:
            yield chunk.text


@app.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Streams tokens to the client as the model generates them, instead of
    waiting for the full response (Phase 1 Topic 09's model.stream(), over HTTP)."""
    return StreamingResponse(_token_generator(request.message), media_type="text/plain")


@app.post("/chat/async", response_model=ChatResponse)
async def chat_async(request: ChatRequest) -> ChatResponse:
    """async def route + await agent.ainvoke(...) - while this call awaits the
    model API over the network, the event loop can serve other requests instead
    of blocking a whole thread on I/O (unlike Topic 03's sync `/chat`)."""
    agent = get_agent()
    result = await agent.ainvoke({"messages": [{"role": "user", "content": request.message}]})
    return ChatResponse(reply=result["messages"][-1].content)


def demo_time_to_first_byte() -> None:
    """Local (non-HTTP) demo: compares when the FIRST token is available from
    a streaming call vs. waiting for a full .invoke() - same point Phase 1
    Topic 09 made, now in the context of what a streaming endpoint gives a client."""
    model = get_model()
    prompt = "In two sentences, explain what an event loop is."

    print("--- streaming: time to first token ---")
    start = time.perf_counter()
    first = None
    for chunk in model.stream(prompt):
        if first is None and chunk.text:
            first = time.perf_counter() - start
    total_stream = time.perf_counter() - start
    print(f"  first token at {first:.2f}s, full stream done at {total_stream:.2f}s")

    print("--- non-streaming: time to any output ---")
    start = time.perf_counter()
    model.invoke(prompt)
    total_invoke = time.perf_counter() - start
    print(f"  first (and only) output at {total_invoke:.2f}s")
    print(
        "\nA streaming client sees text ~"
        f"{max(total_invoke - (first or 0), 0):.2f}s sooner than a non-streaming one, "
        "even though total compute is the same."
    )


def main() -> None:
    require_api_key()
    try:
        import uvicorn
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    demo_time_to_first_byte()

    print("\nStarting API at http://127.0.0.1:8000")
    print("  POST /chat/stream  - StreamingResponse, text/plain token stream")
    print("  POST /chat/async   - async def route, agent.ainvoke()")
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
