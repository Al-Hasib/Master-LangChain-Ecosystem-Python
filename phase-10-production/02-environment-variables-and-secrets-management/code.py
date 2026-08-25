"""
Phase 10 - Topic 02: Environment Variables & Secrets Management

Extends Phase 1 Topic 10's Settings pattern with required-vs-optional validation
that fails fast, at startup, listing every missing required var in one message.

Run:
    python code.py
"""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Declarative required/optional spec. In a real project this table is the
# single source of truth for "what config does this app need" - a new
# teammate reads THIS, not the whole codebase, to set up their .env.
# ============================================================================
REQUIRED_VARS = ["OPENAI_API_KEY"]
OPTIONAL_VARS = {
    "MODEL_NAME": "gpt-4o-mini",
    "LOG_LEVEL": "INFO",
    "APP_ENV": "development",
}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    model_name: str
    log_level: str
    app_env: str

    @classmethod
    def from_env(cls) -> "Settings":
        # Collect ALL problems before exiting - a developer fixing config
        # one sys.exit() at a time is a bad experience. Fail fast, but fail
        # completely, in one message.
        errors: list[str] = []
        values: dict[str, str] = {}

        for var in REQUIRED_VARS:
            val = os.getenv(var)
            if not val:
                errors.append(f"  - {var} is required and not set")
            else:
                values[var] = val

        for var, default in OPTIONAL_VARS.items():
            values[var] = os.getenv(var, default)

        if errors:
            sys.exit(
                "Invalid configuration - missing required environment variable(s):\n"
                + "\n".join(errors)
                + "\n\nFix: 1) cp ../../.env.example ../../.env  2) fill in the key(s) "
                "above  3) re-run.\n"
                "Secrets belong in .env (git-ignored), never committed to code - see "
                "the repo root .gitignore and .env.example."
            )

        return cls(
            openai_api_key=values["OPENAI_API_KEY"],
            model_name=values["MODEL_NAME"],
            log_level=values["LOG_LEVEL"],
            app_env=values["APP_ENV"],
        )

    def redacted(self) -> dict:
        """Never print/log a real secret - this is what a startup banner or
        log line should show instead of the raw Settings object."""
        return {
            "openai_api_key": self.openai_api_key[:3] + "***" if self.openai_api_key else None,
            "model_name": self.model_name,
            "log_level": self.log_level,
            "app_env": self.app_env,
        }


def main() -> None:
    settings = Settings.from_env()

    print("=== Config loaded and validated at startup ===")
    for key, value in settings.redacted().items():
        print(f"  {key:16s} = {value}")

    print(
        "\nNote: openai_api_key is redacted above on purpose - never log full secret "
        "values, even in dev. See doc.md for how this generalizes to a real secrets "
        "manager in staging/production."
    )


if __name__ == "__main__":
    main()
