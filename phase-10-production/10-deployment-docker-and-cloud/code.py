"""
Phase 10 - Topic 10: Deployment: Docker & Cloud

Docker itself isn't available in this sandbox, so this script does NOT run
`docker build`/`docker compose up`. Instead it statically validates that
Dockerfile and docker-compose.yml (in this same folder) are syntactically
sane, then prints the exact commands a developer would run next on a machine
that has Docker installed.

Run:
    python code.py
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

HERE = Path(__file__).parent
DOCKERFILE = HERE / "Dockerfile"
COMPOSE_FILE = HERE / "docker-compose.yml"

REQUIRED_DOCKERFILE_INSTRUCTIONS = ["FROM", "WORKDIR", "COPY", "RUN", "EXPOSE", "CMD"]


def validate_dockerfile(path: Path) -> list[str]:
    """Lightweight structural check - not a Docker parser, just enough to
    catch an obviously broken/incomplete Dockerfile before you burn time on
    `docker build`."""
    problems = []
    if not path.exists():
        return [f"{path.name} not found"]

    text = path.read_text()
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not lines:
        return [f"{path.name} is empty (or only comments)"]

    if not lines[0].upper().startswith("FROM"):
        problems.append("first non-comment instruction must be FROM")

    instructions_present = {line.split()[0].upper() for line in lines if line.split()}
    for required in REQUIRED_DOCKERFILE_INSTRUCTIONS:
        if required not in instructions_present:
            problems.append(f"missing a {required} instruction")

    if "CMD" in instructions_present:
        cmd_lines = [line for line in lines if line.upper().startswith("CMD")]
        if cmd_lines and "0.0.0.0" not in cmd_lines[-1]:
            problems.append(
                "CMD does not bind to 0.0.0.0 - the app would be unreachable from "
                "outside the container (see doc.md Debugging)"
            )

    return problems


def validate_compose_file(path: Path) -> list[str]:
    """Prefers a real YAML parse (pyyaml, already an indirect dependency of
    this repo's LangChain stack) but falls back to a basic structural check
    if pyyaml isn't installed, so this script never hard-fails on that alone."""
    if not path.exists():
        return [f"{path.name} not found"]

    text = path.read_text()

    try:
        import yaml

        parsed = yaml.safe_load(text)
        problems = []
        if not isinstance(parsed, dict) or "services" not in parsed:
            problems.append("no top-level 'services' key")
            return problems
        services = parsed["services"]
        for expected in ("app", "postgres", "redis"):
            if expected not in services:
                problems.append(f"missing expected service: {expected}")
        return problems
    except ImportError:
        # Fallback: crude but dependency-free sanity check.
        problems = []
        if "services:" not in text:
            problems.append("no top-level 'services:' key found")
        for expected in ("app:", "postgres:", "redis:"):
            if f"  {expected}" not in text and f"\t{expected}" not in text:
                problems.append(f"missing expected service block: {expected}")
        return problems
    except Exception as exc:  # yaml.YAMLError etc.
        return [f"YAML parse error: {exc}"]


def main() -> None:
    print("=== Validating Dockerfile ===")
    dockerfile_problems = validate_dockerfile(DOCKERFILE)
    if dockerfile_problems:
        for problem in dockerfile_problems:
            print(f"  [ISSUE] {problem}")
    else:
        print(f"  OK - {DOCKERFILE.name} has FROM/WORKDIR/COPY/RUN/EXPOSE/CMD in a sane shape.")

    print("\n=== Validating docker-compose.yml ===")
    compose_problems = validate_compose_file(COMPOSE_FILE)
    if compose_problems:
        for problem in compose_problems:
            print(f"  [ISSUE] {problem}")
    else:
        print(f"  OK - {COMPOSE_FILE.name} defines app, postgres, and redis services.")

    print(
        "\nNote: Docker itself is not available in this sandbox, so nothing above "
        "actually built or ran a container - this only checked file structure."
    )
    print("\n=== Next steps on a machine with Docker installed ===")
    print("  1) cd to the repo root")
    print("  2) cp .env.example .env   (fill in OPENAI_API_KEY)")
    print(
        "  3) docker compose -f phase-10-production/10-deployment-docker-and-cloud/"
        "docker-compose.yml up --build"
    )
    print("  4) curl http://localhost:8000/health")
    print("  5) docker compose -f .../docker-compose.yml down   # stop and clean up")

    if dockerfile_problems or compose_problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
