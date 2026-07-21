# SafetyMAIN HTTP API

Status: Active  
Date: 2026-07-20

---

## Overview

SafetyMAIN exposes a versioned HTTP API under:

```text
/api/v1
```

The API layer is a thin inbound adapter over Application use cases. Business rules
live in Domain and Application layers.

Authentication and organization membership are **not** implemented yet. Business
requests currently require a temporary organization header.

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [APIFoundation.md](APIFoundation.md) | Factory, health, readiness, errors, request IDs, transactions |
| [KnowledgeObjectAPI.md](KnowledgeObjectAPI.md) | Knowledge Object CRUD, lifecycle, history |
| [KnowledgeObjectSearchAPI.md](KnowledgeObjectSearchAPI.md) | Structured Knowledge Object search |
| [RelationAPI.md](RelationAPI.md) | Relations and traversal endpoints |
| [AuthenticationAPI.md](AuthenticationAPI.md) | Login, refresh, and Bearer auth foundation |

Future authentication design: [AuthenticationArchitecture.md](../architecture/AuthenticationArchitecture.md)

---

## Organization Context

Business endpoints require:

```text
X-Organization-ID: <uuid>
```

System endpoints (`/health`, `/ready`) do not require organization context.

---

## Error Format

All handled errors use:

```json
{
  "error": {
    "code": "request_validation_error",
    "message": "The request is invalid.",
    "details": {
      "request_id": "..."
    }
  }
}
```

Validation failures always return HTTP `422` with code `request_validation_error`.

---

## Request ID

Every response includes:

```text
X-Request-ID
```

Clients may supply their own value. Invalid or overly long values are replaced with
a generated identifier.

---

## OpenAPI and Swagger

| Resource | Path |
|----------|------|
| OpenAPI JSON | `/openapi.json` |
| Swagger UI | `/docs` |

Operation IDs are stable and suitable for generated clients. See
[APIFoundation.md](APIFoundation.md) for contract details.

---

## Current Limitations

- No authentication or authorization
- No organization membership enforcement
- No rate limiting or idempotency keys
- No cursor pagination or full-text search
- Live PostgreSQL HTTP integration tests are not part of the current suite

Repository contract tests define PostgreSQL behavior separately. Live PostgreSQL
validation for migrations and DB-backed readiness remains a follow-up operational step.

---

## Local Run

```bash
python3 -m uvicorn backend.api.app:app --reload
```

See `.env.example` for recommended environment variables.
