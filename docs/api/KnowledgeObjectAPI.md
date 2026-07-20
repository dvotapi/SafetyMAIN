# Knowledge Object HTTP API

Status: Active  
Date: 2026-07-19

---

## Overview

Knowledge Object operations are exposed under the versioned API prefix:

```text
/api/v1/knowledge-objects
```

The HTTP layer is a thin inbound adapter. Business rules remain in Domain and Application handlers.

Search and collection listing are documented in [KnowledgeObjectSearchAPI.md](KnowledgeObjectSearchAPI.md).

---

## Organization Context

Every Knowledge Object request requires:

```text
X-Organization-ID: <uuid>
```

This header is temporary transport context until authentication and organization membership are introduced.

Cross-organization access is rejected as `404 Not Found` with code `knowledge_object_not_found` so callers cannot infer whether an object exists in another organization.

---

## Routes

| Method | Path | Success | Description |
|--------|------|---------|-------------|
| `GET` | `/api/v1/knowledge-objects` | `200` | Structured search |
| `POST` | `/api/v1/knowledge-objects` | `201` | Create |
| `GET` | `/api/v1/knowledge-objects/{id}` | `200` | Get current version |
| `PUT` | `/api/v1/knowledge-objects/{id}` | `200` | Update with versioning |
| `POST` | `/api/v1/knowledge-objects/{id}/archive` | `200` | Archive |
| `POST` | `/api/v1/knowledge-objects/{id}/restore` | `200` | Restore |
| `DELETE` | `/api/v1/knowledge-objects/{id}` | `204` | Soft delete |
| `GET` | `/api/v1/knowledge-objects/{id}/history` | `200` | Previous versions only |

Successful create responses include:

```text
Location: /api/v1/knowledge-objects/{id}
```

Delete returns an empty body.

---

## Create Request

```json
{
  "type": "policy",
  "metadata": {
    "title": "Information Security Policy"
  }
}
```

Client-controlled fields such as ID, version, status, and timestamps are rejected or ignored by design.

---

## Update Request

```json
{
  "version": 1,
  "metadata": {
    "title": "Updated Information Security Policy"
  }
}
```

`version` is the expected **current** version (optimistic concurrency). The Application layer increments the version; routers do not.

Stale or jumped versions return `409 Conflict` with code `knowledge_object_version_conflict`.

---

## Response

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "type": "policy",
  "status": "draft",
  "version": 1,
  "metadata": {
    "title": "Information Security Policy"
  },
  "created_at": "2026-07-19T10:00:00+00:00",
  "updated_at": "2026-07-19T10:00:00+00:00"
}
```

Domain entities and ORM models are never returned directly.

---

## History Semantics

`GET .../history` returns **previous versions only**:

- current version is excluded;
- version-1 objects return `"items": []`;
- ordering is oldest to newest;
- archived and deleted historical states are serialized as stored.

---

## Lifecycle Notes

- **Delete** is a soft delete. Objects remain internally persisted.
- Deleted objects cannot be updated, archived, or restored.
- Repeated delete returns `409 Conflict` (`knowledge_object_already_deleted`).

---

## Error Format

Errors use the common API envelope documented in [APIFoundation.md](APIFoundation.md).

Representative domain mappings:

| Condition | HTTP | Code |
|-----------|------|------|
| Not found / cross-org | `404` | `knowledge_object_not_found` |
| Duplicate / lifecycle conflict | `409` | domain-specific code |
| Version conflict | `409` | `knowledge_object_version_conflict` |
| Invalid request | `422` | `request_validation_error` |

Every response includes `X-Request-ID`.

---

## Transaction Ownership

Command handlers call `unit_of_work.commit()` after successful mutations.

Query handlers do not commit.

The FastAPI Unit of Work dependency never commits on successful HTTP responses.

---

## Local Example

```bash
curl -sS \
  -H "X-Organization-ID: 00000000-0000-0000-0000-000000000001" \
  -H "Content-Type: application/json" \
  -d '{"type":"policy","metadata":{"title":"Example"}}' \
  http://127.0.0.1:8000/api/v1/knowledge-objects
```

See also [APIFoundation.md](APIFoundation.md) for application factory and dependency override strategy.
