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

If the worker or Redis was down, re-queue tickets stuck for more than
10 minutes with:

```bash
uv run python manage.py requeue_stale_tickets
```

## Running tests

```bash
uv run pytest
```

Postgres and Redis must be running.

## API

Create a ticket:

```bash
curl -i -X POST http://localhost:8000/api/tickets/ \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "c-0001", "text": "My card still has not arrived"}'
```

The response is `202 Accepted`, with the ticket in the body and its address in
the `Location` header. Check the result with:

```bash
curl http://localhost:8000/api/tickets/<id>/
```
