# Knowledge Object Search HTTP API

Status: Active  
Date: 2026-07-19

---

## Overview

Structured Knowledge Object search is exposed on the collection route:

```text
GET /api/v1/knowledge-objects
```

The HTTP layer parses query parameters, builds an Application search query, and maps repository-backed results into the standard Knowledge Object response schema.

Filtering, ordering, and total calculation remain inside repository search implementations.

See also: [KnowledgeObjectAPI.md](KnowledgeObjectAPI.md) for create, read, update, archive, restore, delete, and history routes.

---

## Organization Context

Every search request requires:

```text
X-Organization-ID: <uuid>
```

Invalid header values return `422 Unprocessable Entity` with code `request_validation_error`.

Organization ID is never accepted as a query parameter. Results are always scoped to the requested organization.

---

## Query Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `type` | No | none | Exact Knowledge Object type filter |
| `status` | No | none | Lifecycle status filter |
| `metadata` | No | none | URL-encoded JSON object with metadata equality filters |
| `include_deleted` | No | `false` | Include deleted objects when no explicit status excludes them |
| `offset` | No | `0` | Pagination offset (`>= 0`) |
| `limit` | No | `50` | Page size (`1..100`) |

Example:

```text
GET /api/v1/knowledge-objects?type=policy&status=active&metadata={"department":"security","approved":true}&offset=0&limit=50
```

---

## Metadata Filter Format

`metadata` must be a single JSON object encoded in the query string.

Example decoded value:

```json
{
  "department": "security",
  "approved": true,
  "revision": 3
}
```

Requirements:

- optional parameter;
- top-level value must be a JSON object;
- top-level arrays, strings, numbers, booleans, and `null` are rejected;
- nested values may use valid JSON types;
- JSON value types are preserved exactly;
- all metadata keys are combined with **AND** semantics;
- an empty object `{}` is valid and applies no metadata constraints;
- duplicate object keys are rejected with `422`;
- invalid JSON returns `422`;
- `NaN`, `Infinity`, and `-Infinity` are rejected;
- parsing uses strict JSON decoding (not Python literal evaluation).

Type-sensitive examples that do **not** match each other:

```json
{"approved": true}
{"approved": 1}
{"approved": "true"}
```

---

## Lifecycle Status Values

Public HTTP values are lowercase:

| HTTP value | Meaning |
|------------|---------|
| `active` | Active objects |
| `archived` | Archived objects |
| `deleted` | Deleted objects |

Invalid status values return `422`.

---

## Deleted Object Behavior

Default behavior excludes deleted objects unless the search criteria explicitly allow them.

| Request | Behavior |
|---------|----------|
| no `status`, `include_deleted=false` | active and archived only |
| no `status`, `include_deleted=true` | active, archived, and deleted |
| `status=active`, `include_deleted=false` | active only |
| `status=archived`, `include_deleted=false` | archived only |
| `status=deleted` ( `include_deleted` omitted ) | deleted only |
| `status=deleted`, `include_deleted=true` | deleted only |
| `status=deleted`, `include_deleted=false` | rejected with `422` |

Draft objects are never returned by default collection search and are not included by `include_deleted=true`.

---

## Pagination

Pagination uses offset and limit:

- default `offset=0`;
- default `limit=50`;
- maximum `limit=100`;
- negative offset, zero limit, and limit above 100 return `422`.

`pagination.total` is the number of matching objects **before** pagination is applied.

Ordering is deterministic and follows repository search ordering (`created_at` ascending, then `id` ascending).

---

## Success Response

```json
{
  "items": [
    {
      "id": "uuid",
      "organization_id": "uuid",
      "type": "policy",
      "status": "active",
      "version": 2,
      "metadata": {
        "department": "security"
      },
      "created_at": "2026-07-19T10:00:00Z",
      "updated_at": "2026-07-19T11:00:00Z"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 50,
    "total": 1
  }
}
```

Each item uses the same schema as other Knowledge Object read endpoints.

---

## Validation Error Example

```json
{
  "error": {
    "code": "request_validation_error",
    "message": "The request is invalid.",
    "details": {}
  }
}
```

---

## Example Requests

Active policy search:

```bash
curl -G \
  -H "X-Organization-ID: <org-uuid>" \
  --data-urlencode 'type=policy' \
  --data-urlencode 'status=active' \
  --data-urlencode 'metadata={"department":"security","approved":true}' \
  --data-urlencode 'offset=0' \
  --data-urlencode 'limit=50' \
  http://127.0.0.1:8000/api/v1/knowledge-objects
```

Include deleted objects:

```bash
curl -G \
  -H "X-Organization-ID: <org-uuid>" \
  --data-urlencode 'include_deleted=true' \
  http://127.0.0.1:8000/api/v1/knowledge-objects
```

Deleted-only search:

```bash
curl -G \
  -H "X-Organization-ID: <org-uuid>" \
  --data-urlencode 'status=deleted' \
  http://127.0.0.1:8000/api/v1/knowledge-objects
```

---

## Route Ordering

Both routes resolve independently:

```text
GET /api/v1/knowledge-objects
GET /api/v1/knowledge-objects/{knowledge_object_id}
```

The collection route performs structured search. The detail route returns one object by ID.

---

## Testing Notes

HTTP tests run without PostgreSQL using:

```text
FastAPI → SearchKnowledgeObjectsHandler → InMemoryUnitOfWork → InMemoryKnowledgeObjectRepository
```

Live PostgreSQL validation for this HTTP endpoint is not part of the current test suite. Repository contract tests define PostgreSQL search behavior separately.
