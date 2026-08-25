"""
Phase 10 - Topic 06: Databases: PostgreSQL & Redis

Real psycopg (Postgres) and redis-py (Redis) client code for conversation storage
and response caching. This sandbox has neither database running, so connection
attempts are wrapped in try/except - catching the connection error specifically
and printing the docker run command to start one locally, never a raw traceback.

Run:
    python code.py
"""

import hashlib
import sys
import time

from dotenv import load_dotenv

load_dotenv()


POSTGRES_HELP = (
    "Could not connect to PostgreSQL.\n"
    "Start one locally with:\n"
    "  docker run -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres\n"
    "Then set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres in .env"
)
REDIS_HELP = (
    "Could not connect to Redis.\n"
    "Start one locally with:\n"
    "  docker run -p 6379:6379 redis\n"
    "Then set REDIS_URL=redis://localhost:6379/0 in .env"
)


# ============================================================================
# PostgreSQL - durable conversation storage (real psycopg, same shape as
# Topic 05's SQLite store, so an app can be migrated from one to the other
# without changing the calling code's interface).
#
# LangGraph sidebar: if the app calls a LangGraph graph directly (rather than
# via create_agent's default in-memory checkpointing), the graph-native way to
# persist run state to Postgres is `langgraph.checkpoint.postgres.PostgresSaver`
# (from the `langgraph-checkpoint-postgres` package) - a BaseCheckpointSaver
# passed as `checkpointer=` to `graph.compile(...)`. That persists LangGraph's
# own state machine, not just chat turns; the plain-table approach below is
# what you'd use for a hand-rolled memory layer instead.
# ============================================================================
class PostgresConversationStore:
    def __init__(self, dsn: str = "postgresql://postgres:postgres@localhost:5432/postgres"):
        self.dsn = dsn

    def _connect(self):
        import psycopg  # real dependency: psycopg[binary]

        return psycopg.connect(self.dsn, connect_timeout=3)

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
                """
            )

    def append(self, session_id: str, role: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (%s, %s, %s)",
                (session_id, role, content),
            )

    def history(self, session_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE session_id = %s ORDER BY id",
                (session_id,),
            ).fetchall()
        return [{"role": r, "content": c} for r, c in rows]


def demo_postgres() -> None:
    print("=== PostgreSQL conversation store ===")
    store = PostgresConversationStore()
    try:
        store.init_schema()
        store.append("session-1", "user", "Hello from Topic 06.")
        history = store.history("session-1")
        print(f"History: {history}")
    except ImportError:
        print("Missing dependency. Run: pip install -r ../../requirements.txt (uncomment psycopg)")
    except Exception as exc:  # psycopg.OperationalError etc. - connection issues
        print(POSTGRES_HELP)
        print(f"(underlying error: {exc.__class__.__name__}: {exc})")


# ============================================================================
# Redis - fast, shared response cache (real redis-py). A cache is allowed to
# be unavailable without breaking the app - callers should treat a Redis
# failure as a cache miss, never as a fatal error.
# ============================================================================
class ResponseCache:
    def __init__(self, url: str = "redis://localhost:6379/0", ttl_seconds: int = 3600):
        self.url = url
        self.ttl_seconds = ttl_seconds
        self._client = None

    def _client_or_none(self):
        if self._client is not None:
            return self._client
        import redis  # real dependency: redis[hiredis] or plain redis

        client = redis.Redis.from_url(self.url, socket_connect_timeout=3)
        client.ping()  # fail fast here, not on first get/set
        self._client = client
        return self._client

    @staticmethod
    def _key(prompt: str) -> str:
        return "chatcache:" + hashlib.sha256(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> str | None:
        client = self._client_or_none()
        value = client.get(self._key(prompt))
        return value.decode() if value is not None else None

    def set(self, prompt: str, response: str) -> None:
        client = self._client_or_none()
        client.setex(self._key(prompt), self.ttl_seconds, response)


def demo_redis() -> None:
    print("\n=== Redis response cache ===")
    cache = ResponseCache()
    try:
        prompt = "What is 2 + 2?"
        cached = cache.get(prompt)
        if cached is None:
            print("Cache miss - would call the model here")
            cache.set(prompt, "4")
            print("Stored response in cache")
        else:
            print(f"Cache hit: {cached}")
    except ImportError:
        print("Missing dependency. Run: pip install -r ../../requirements.txt (uncomment redis)")
    except Exception as exc:  # redis.exceptions.ConnectionError etc.
        print(REDIS_HELP)
        print(f"(underlying error: {exc.__class__.__name__}: {exc})")


def main() -> None:
    demo_postgres()
    demo_redis()
    print(
        "\nBoth demos degrade to setup instructions (not a crash) when the "
        "corresponding database isn't running locally - see doc.md Debugging."
    )


if __name__ == "__main__":
    main()
