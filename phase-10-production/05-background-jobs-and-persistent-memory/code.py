"""
Phase 10 - Topic 05: Background Jobs & Persistent Memory

Part 1: a FastAPI endpoint using BackgroundTasks to do work AFTER the response
         is sent (logging usage), so the client doesn't wait for it.
Part 2: a SQLite-backed conversation store (stdlib sqlite3) that survives a
         simulated process restart - Topic 06 does the same thing against Postgres.

Run:
    python code.py                 # runs the SQLite memory demo, then serves the API
    uvicorn code:app --reload      # API only
"""

import os
import sqlite3
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

try:
    from fastapi import BackgroundTasks, FastAPI
    from pydantic import BaseModel, Field
except ImportError:
    sys.exit(
        "Missing dependency. Run: pip install -r ../../requirements.txt\n"
        "(fastapi/uvicorn are commented out in requirements.txt for Phase 10 - "
        "uncomment them, or: pip install fastapi uvicorn)"
    )


# ============================================================================
# Part 2: persistent memory (SQLite, stdlib only - no server required).
# In production this becomes Topic 06's Postgres-backed version once more
# than one API instance needs to share the same conversation state.
# ============================================================================
DB_PATH = Path(__file__).parent / "conversations.db"


class SQLiteMemoryStore:
    """Conversation memory keyed by session_id. Opens/closes a connection per
    call rather than holding one open - simplest correct pattern for SQLite,
    and mirrors how a Postgres connection pool is used in Topic 06."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )

    def append(self, session_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (session_id, role, content, time.time()),
            )

    def history(self, session_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        return [{"role": role, "content": content} for role, content in rows]


def demo_memory_survives_restart() -> None:
    print("=== Persistent memory demo (SQLite) ===")
    if DB_PATH.exists():
        DB_PATH.unlink()  # clean slate for the demo

    # "Process 1": store a turn, then let the store object go out of scope.
    store_a = SQLiteMemoryStore()
    store_a.append("session-1", "user", "My name is Ada.")
    store_a.append("session-1", "assistant", "Nice to meet you, Ada.")
    del store_a

    # "Process 2": a brand-new store instance (simulating a restart) opens
    # the same file and finds the prior conversation still there.
    store_b = SQLiteMemoryStore()
    history = store_b.history("session-1")
    print(f"History for session-1 after 'restart': {history}")
    assert len(history) == 2, "memory did not survive the simulated restart"
    print("Memory survived the simulated restart - stored in", DB_PATH)


# ============================================================================
# Part 1: background work (FastAPI BackgroundTasks) - runs AFTER the
# response is returned, so the client isn't slowed down by it.
# ============================================================================
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str


app = FastAPI(title="Phase 10 Topic 05 - Background Jobs & Memory")
_store = SQLiteMemoryStore()


def log_usage(session_id: str, message: str) -> None:
    """Best-effort, off the request path. If this were slow (an analytics
    API call, a notification), the client would never notice - it already
    has its response by the time this runs."""
    print(f"[background] logged usage for session={session_id!r} chars={len(message)}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    if not os.getenv("OPENAI_API_KEY"):
        return ChatResponse(reply="(stub - set OPENAI_API_KEY to call the real model)")

    from langchain.chat_models import init_chat_model

    model = init_chat_model("gpt-4o-mini", model_provider="openai", temperature=0)
    _store.append(request.session_id, "user", request.message)
    history = _store.history(request.session_id)

    response = model.invoke([{"role": m["role"], "content": m["content"]} for m in history])
    _store.append(request.session_id, "assistant", response.content)

    # Scheduled to run AFTER the response is sent - not awaited, not blocking.
    background_tasks.add_task(log_usage, request.session_id, request.message)

    return ChatResponse(reply=response.content)


def main() -> None:
    demo_memory_survives_restart()

    try:
        import uvicorn
    except ImportError:
        sys.exit("Missing dependency. Run: pip install -r ../../requirements.txt")

    print("\nStarting API at http://127.0.0.1:8000  (POST /chat uses BackgroundTasks + SQLite memory)")
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
