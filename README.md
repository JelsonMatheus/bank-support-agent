# Bank Support Agent

An LLM-powered support agent for a fictional digital bank. It classifies
customer messages, answers from a knowledge base with citations, or hands off
to a human when it shouldn't answer.

> **Status:** work in progress.

## Running locally

Requirements: [uv](https://docs.astral.sh/uv/) and Docker.

```bash
cp .env.example .env    # fill in the empty values (see comments in the file)
docker compose up -d    # Postgres (pgvector) on port 5433 and Redis on 6379
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

In a second terminal, start the worker:

```bash
uv run celery -A config worker -l info
```

Check that everything is up at http://localhost:8000/health/.

## Running tests

```bash
uv run pytest
```

Postgres and Redis must be running.