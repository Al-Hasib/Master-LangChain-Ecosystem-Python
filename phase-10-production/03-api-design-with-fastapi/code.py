"""
Phase 10 - Topic 03: API Design with FastAPI

Wraps a single create_agent(...) call in a FastAPI app with one POST /chat endpoint
and a GET /health endpoint.

Run (two options - both work):
    uvicorn code:app --reload      # standard dev-server way (auto-reload)
    python code.py                 # also works - runs uvicorn.run(...) internally
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

try:
    from fastapi import FastAPI
    from pydantic import BaseModel, Field
except ImportError:
    sys.exit(
        "Missing dependency. Run: pip install -r ../../requirements.txt\n"
        "(fastapi/uvicorn are listed but commented out in requirements.txt for "
        "Phase 10 - uncomment them, or: pip install fastapi uvicorn)"
    )


# ============================================================================
# Request/response contract - Pydantic models. This shape stays stable even
# as the agent behind it changes (new tools, new model, new prompt).
# ============================================================================
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    session_id: str = Field(default="default", description="Conversation/session id")


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class HealthResponse(BaseModel):
    status: str
    model: str


# ============================================================================
# Agent construction - one place, built lazily so importing this module (e.g.
# for tests, or `uvicorn code:app`) doesn't require an API key just to import.
# ============================================================================
_agent = None
MODEL_NAME = "gpt-4o-mini"


def get_agent():
    global _agent
    if _agent is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "Missing OPENAI_API_KEY.\n1) cp ../../.env.example ../../.env\n"
                "2) fill in your key\n3) re-run"
            )
        from langchain.agents import create_agent

        _agent = create_agent(model=MODEL_NAME, tools=[], system_prompt="You are a helpful assistant.")
    return _agent


# ============================================================================
# The FastAPI app. Must be a module-level variable named `app` for
# `uvicorn code:app` to find it.
# ============================================================================
app = FastAPI(title="Phase 10 Topic 03 - Minimal LLM API", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Standard liveness endpoint - Topic 10's Docker/orchestrator health
    checks call this to know the process is up (not necessarily that the
    model call works, which would cost money on every health check)."""
    return HealthResponse(status="ok", model=MODEL_NAME)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Route handler stays thin: validate (Pydantic already did this),
    delegate to the agent, shape the response. No business logic here."""
    agent = get_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": request.message}]})
    reply = result["messages"][-1].content
    return ChatResponse(reply=reply, session_id=request.session_id)


def main() -> None:
    """`python code.py` also works end-to-end - starts uvicorn programmatically
    instead of requiring the `uvicorn code:app` CLI form."""
    try:
        import uvicorn
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    print("Starting API at http://127.0.0.1:8000  (docs at /docs, health at /health)")
    print('Try: curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" '
          '-d "{\\"message\\": \\"Hello\\"}"')
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
