# Phase 10 - Topic 10: Dockerfile for the Topic 03 FastAPI app.
# Single-stage, kept simple and correct rather than size-optimized - see
# doc.md Production notes for what a leaner/multi-stage build would add.

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout - both matter
# for clean container logs (unbuffered output shows up in `docker logs`
# immediately instead of being held until the buffer flushes).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the dependency list first so Docker's layer cache is reused on
# every rebuild that doesn't touch requirements.txt - the slow `pip install`
# step is skipped unless dependencies actually changed.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code.
COPY phase-10-production/03-api-design-with-fastapi/code.py ./code.py

# Document the port the app listens on (informational - the actual publish
# happens via `-p` on `docker run` or `ports:` in docker-compose.yml).
EXPOSE 8000

# Bind to 0.0.0.0, not 127.0.0.1 - a container's loopback address isn't
# reachable from outside the container, so the app must listen on all
# interfaces to be reachable via the published port.
CMD ["uvicorn", "code:app", "--host", "0.0.0.0", "--port", "8000"]
