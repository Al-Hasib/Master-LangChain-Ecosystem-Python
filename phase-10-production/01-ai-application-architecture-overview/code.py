"""
Phase 10 - Topic 01: AI Application Architecture Overview

Not a working app - an "architecture as code" skeleton. Each method below is a stub
for a concern that gets a real implementation in a later topic. Running this prints the
request lifecycle in the order the layers actually execute, so the shape is visible
before any topic supplies the substance.

Run:
    python code.py
"""

import sys
import time
from dataclasses import dataclass, field


# ============================================================================
# config.py equivalent (Topic 02 fills this in for real, with validation)
# ============================================================================
@dataclass(frozen=True)
class Settings:
    app_name: str = "production-rag-service"
    model_name: str = "gpt-4o-mini"


# ============================================================================
# The skeleton itself. Every method here is a HOOK POINT - it names the topic
# that turns it into real code, and does nothing but log that it ran.
# ============================================================================
@dataclass
class App:
    settings: Settings
    log: list = field(default_factory=list)

    def _step(self, name: str, note: str) -> None:
        self.log.append(f"[{name}] {note}")

    # --- Topic 07: reject unauthenticated / over-limit requests before any
    # model call happens - cheapest place to stop abuse.
    def authenticate_and_rate_limit(self, api_key: str) -> None:
        self._step("auth+rate-limit (07)", f"validate api_key={api_key!r}, check bucket")

    # --- Topic 07: serve from cache if this exact prompt was answered
    # recently - skips the model call entirely.
    def check_cache(self, prompt: str) -> str | None:
        self._step("cache (07)", f"lookup cache for prompt hash of {prompt!r}")
        return None  # cache miss in this skeleton

    # --- Topic 06: read/write durable conversation state so the agent has
    # memory across requests, not just within one process's lifetime.
    def load_memory(self, session_id: str) -> list:
        self._step("memory/postgres (05/06)", f"load prior turns for session={session_id}")
        return []

    # --- Topic 03/04: the actual LangChain/LangGraph call. Sync here;
    # Topic 04 shows the async + streaming version of this exact hook.
    def call_agent(self, prompt: str) -> str:
        self._step("agent call (03/04)", f"model={self.settings.model_name} invoke(...)")
        return f"(stub response to: {prompt})"

    # --- Topic 05: anything that shouldn't block the HTTP response (e.g.
    # writing analytics, sending a notification) goes here, off the request path.
    def enqueue_background_work(self) -> None:
        self._step("background job (05)", "enqueue: log usage, update analytics")

    # --- Topic 08: every call gets measured so cost/latency regressions are
    # visible before they become a production incident.
    def record_cost_and_latency(self, elapsed: float) -> None:
        self._step("cost/latency (08)", f"elapsed={elapsed:.4f}s recorded to metrics store")

    def handle_request(self, api_key: str, session_id: str, prompt: str) -> str:
        """One request, walking every hook point in the order it would fire
        in the real app (see doc.md diagram)."""
        start = time.perf_counter()

        self.authenticate_and_rate_limit(api_key)

        cached = self.check_cache(prompt)
        if cached is not None:
            self._step("cache (07)", "HIT - returning cached response, skipping agent call")
            return cached

        self.load_memory(session_id)
        response = self.call_agent(prompt)
        self.enqueue_background_work()
        self.record_cost_and_latency(time.perf_counter() - start)
        return response


def main() -> None:
    settings = Settings()
    app = App(settings=settings)

    print(f"=== {settings.app_name} - request lifecycle (skeleton) ===\n")
    response = app.handle_request(
        api_key="demo-key", session_id="session-1", prompt="What's in the Q3 report?"
    )

    for line in app.log:
        print(line)
    print(f"\nfinal response: {response!r}")
    print(
        "\nEach [label] above names the topic that replaces the stub with real code. "
        "Topics 02-10 build those, one at a time."
    )


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        sys.exit("This example uses `str | None` syntax - requires Python 3.10+.")
    main()
