# Booking Rules Demo

> **A standalone FastAPI + PostgreSQL reference implementation for conflict-safe resource bookings.**  
> Built as a public technical demo. No client code, data, credentials, or production configuration is included.

![Python](https://img.shields.io/badge/Python-3.12-0D1214?style=flat&logo=python&logoColor=E4A244)
![FastAPI](https://img.shields.io/badge/FastAPI-0D1214?style=flat&logo=fastapi&logoColor=58A79C)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-0D1214?style=flat&logo=postgresql&logoColor=E4A244)
![Docker](https://img.shields.io/badge/Docker-0D1214?style=flat&logo=docker&logoColor=58A79C)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-0D1214?style=flat&logo=githubactions&logoColor=58A79C)

## Why this exists

A booking system must prevent the most expensive operational failure: two confirmed reservations occupying the same resource at overlapping times. Application-level validation alone is insufficient because concurrent requests can pass the same pre-check. This demo treats conflict prevention as a database responsibility and keeps the booking rules explicit, testable, and observable.

## What it demonstrates

| Area | Implementation |
|---|---|
| Domain rules | UTC-aware intervals, non-negative buffers, and a strict end-after-start invariant |
| API | A small FastAPI service for creating resources and booking them |
| Data integrity | A PostgreSQL exclusion constraint that rejects overlapping active bookings for a resource |
| Lifecycle | `pending_payment`, `confirmed`, `cancelled`, and `completed` statuses |
| Testing | Unit tests for interval rules and API integration tests against SQLite-compatible paths |
| Local runtime | Docker Compose with PostgreSQL 16 and one API command |
| CI | Ruff linting, type checking, and tests on every push and pull request |

## Architecture

```text
HTTP request
    ↓
FastAPI route
    ↓
Domain validation ─── rejects invalid intervals and invalid buffers
    ↓
SQLAlchemy transaction
    ↓
PostgreSQL bookings_no_overlap_resource exclusion constraint
    ↓
201 Created or 409 Conflict
```

The critical concurrency guarantee is the PostgreSQL constraint in `migrations/001_initial.sql`. SQLite is used only for lightweight API test coverage; the exclusion constraint requires PostgreSQL in real deployments.

## Run locally

```bash
git clone https://github.com/artyomliske/booking-rules-demo.git
cd booking-rules-demo
cp .env.example .env
docker compose up --build
```

The API becomes available at `http://localhost:8000`, with interactive documentation at `http://localhost:8000/docs`.

## API example

Create a resource:

```bash
curl -X POST http://localhost:8000/resources \
  -H 'content-type: application/json' \
  -d '{"name":"Studio A"}'
```

Create a booking with a 15-minute cleanup buffer:

```bash
curl -X POST http://localhost:8000/bookings \
  -H 'content-type: application/json' \
  -d '{
    "resource_id": 1,
    "starts_at": "2026-09-01T10:00:00Z",
    "ends_at": "2026-09-01T12:00:00Z",
    "buffer_before_min": 0,
    "buffer_after_min": 15
  }'
```

A second active booking whose occupied interval overlaps this one returns `409 Conflict`.

## Test and quality checks

```bash
pip install -e '.[dev]'
ruff check .
mypy app
pytest
```

## Project structure

```text
app/
  api/           HTTP routes and request/response schemas
  domain/        Pure booking interval rules
  infra/         Database engine and SQLAlchemy models
migrations/      PostgreSQL schema and exclusion constraint
tests/           Domain and API tests
.github/         Continuous integration workflow
```

## Scope and limitations

This is intentionally small. It does not implement authentication, payments, retries, multi-tenant isolation, or a UI. Those concerns are meaningful in a production system but would obscure the central demonstration: how to make scheduling conflicts impossible to persist.

## License

MIT

[View the full portfolio case →](https://artyomliske.ru/#case-booking)
