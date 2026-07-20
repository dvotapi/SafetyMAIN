# SafetyMAIN API Foundation

Status: Active  
Date: 2026-07-19

---

## Purpose

This document describes the HTTP API foundation for SafetyMAIN.

The API layer is an inbound adapter. It exposes process health, readiness, and
shared transport concerns. Business endpoints for Knowledge Objects and Relations
are intentionally out of scope for this foundation.

---

## Application Factory

The FastAPI application is created by an explicit factory:

```python
from backend.api.app import create_app

application = create_app()
```

Requirements:

- importing `backend.api.app` does not connect to PostgreSQL;
- importing the module does not open a SQLAlchemy `Session`;
- importing the module does not create tables or apply migrations;
- tests may create isolated application instances with overridden settings and dependencies.

A thin default instance is exported for Uvicorn:

```python
app = create_app()
```

---

## Local Run

```bash
python3 -m uvicorn backend.api.app:app --reload
```

Recommended environment variables are listed in `.env.example`.

---

## API Prefix

Versioned API root:

```text
/api/v1
```

Current system routes:

```text
GET /api/v1/health
GET /api/v1/ready
```

Knowledge Object routes are documented in [KnowledgeObjectAPI.md](KnowledgeObjectAPI.md).

Knowledge Object structured search is documented in [KnowledgeObjectSearchAPI.md](KnowledgeObjectSearchAPI.md).

Relation routes are documented in [RelationAPI.md](RelationAPI.md).

Reserved for future business routers:

```text
/api/v1/relations
```

---

## Health Semantics

`GET /api/v1/health` reports whether the web process is running.

- HTTP `200` on success;
- does not access the database;
- does not expose secrets, environment dumps, or database URLs.

Example:

```json
{
  "status": "ok",
  "service": "SafetyMAIN API",
  "version": "0.1.0"
}
```

---

## Readiness Semantics

`GET /api/v1/ready` reports whether required infrastructure is reachable.

For production wiring the check executes a minimal PostgreSQL probe:

```sql
SELECT 1
```

The check must not:

- run migrations;
- create schema;
- modify data;
- expose raw driver or database error text.

Success:

```json
{
  "status": "ready"
}
```

Failure (HTTP `503`):

```json
{
  "error": {
    "code": "service_not_ready",
    "message": "The service is not ready.",
    "details": {
      "request_id": "..."
    }
  }
}
```

In tests, readiness is injected through FastAPI dependency overrides so PostgreSQL
is not required.

---

## Error Response Format

All handled API errors use a common immutable shape:

```json
{
  "error": {
    "code": "knowledge_object_not_found",
    "message": "Knowledge Object was not found.",
    "details": {
      "request_id": "..."
    }
  }
}
```

`details` is always present on handled errors. When no additional fields exist, it
contains at least the request identifier:

```json
{
  "request_id": "..."
}
```

Public responses never include:

- stack traces;
- SQL statements;
- database URLs;
- driver error details;
- Python class paths.

Request validation errors use code `request_validation_error`, HTTP `422`, and
message `The request is invalid.`

Validation details use a normalized structure:

```json
{
  "error": {
    "code": "request_validation_error",
    "message": "The request is invalid.",
    "details": {
      "violations": [
        {
          "location": ["query", "limit"],
          "message": "Input should be less than or equal to 100",
          "type": "less_than_equal"
        }
      ],
      "request_id": "..."
    }
  }
}
```

Unexpected exceptions use code `internal_server_error`, HTTP `500`, and a generic
public message. Internal exception text remains in application logs only.

---

## Request ID Behavior

- Clients may send `X-Request-ID`.
- When absent, invalid, or excessively long, the API generates a request ID.
- Every response includes `X-Request-ID`.
- Exception handlers can read the request ID from request state and may include it
  in error `details`.

---

## Dependency Override Strategy

Production wiring is assembled in `backend.bootstrap.container`.

Tests should replace dependencies with FastAPI overrides, for example:

- `get_settings`
- `get_readiness_check`
- `get_uow` / `get_uow_factory`

HTTP foundation tests must run without a live PostgreSQL database.

Do not monkeypatch private SQLAlchemy internals in API tests.

---

## Transaction Ownership

The request-scoped Unit of Work dependency:

```python
with uow_factory() as uow:
    yield uow
```

guarantees context-manager entry and exit for each request that needs a UoW.

It does **not** commit automatically when the HTTP response succeeds.

Commit and rollback decisions belong to application use cases and the existing
Unit of Work contract.

---

## Why Migrations Are Not Run at Startup

Application startup must remain side-effect free with respect to schema ownership:

- schema evolution is an operational concern managed by Alembic;
- API processes should not mutate database structure on boot;
- readiness only verifies connectivity, not migration state;
- this keeps imports, tests, and process restarts deterministic.

---

## Composition Root Exception

`backend.bootstrap` may import concrete Infrastructure implementations.

API routers must not import SQLAlchemy ORM models or concrete repository classes
directly. They depend on contracts and injectable factories.

---

## OpenAPI

FastAPI generates the OpenAPI document at `/openapi.json`.

Interactive docs are available at `/docs`.

System endpoints are tagged `System`.

Business routes document stable `operationId` values, common error schemas,
`X-Organization-ID` on organization-scoped routes, `Location` on create responses,
and `X-Request-ID` on success and no-content responses.

See [README.md](README.md) for the API documentation index.
