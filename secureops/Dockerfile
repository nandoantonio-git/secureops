# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

WORKDIR /build

# System build deps for any package without a prebuilt wheel on this
# platform (psycopg[binary] and the tree-sitter grammars normally ship
# wheels, but keep a compiler available so a missing wheel fails to build
# cleanly instead of failing to import at runtime).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:${PATH}"

COPY --from=builder /install /usr/local
COPY app ./app
COPY alembic.ini ./
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Runs as a non-root user; the app only reads its own source and talks to
# Postgres/Ollama over the network, no local files need to be writable.
RUN useradd --create-home --uid 1000 secureops
USER secureops

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
