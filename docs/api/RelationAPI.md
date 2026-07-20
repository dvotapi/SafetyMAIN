# Knowledge Object Relation HTTP API

Status: Active  
Date: 2026-07-19

---

## Overview

Relation operations are exposed under:

```text
/api/v1/relations
```

One-hop traversal endpoints are scoped by Knowledge Object:

```text
GET /api/v1/knowledge-objects/{id}/relations/outgoing
GET /api/v1/knowledge-objects/{id}/relations/incoming
GET /api/v1/knowledge-objects/{id}/connected
```

Recursive graph traversal is **not** supported.

---

## Organization Context

Every request requires:

```text
X-Organization-ID: <uuid>
```

Cross-organization access to objects or relations returns `404 Not Found` with code
`knowledge_object_not_found` or `knowledge_object_relation_not_found`.

---

## Create Relation

```http
POST /api/v1/relations
```

Request:

```json
{
  "source_object_id": "uuid",
  "target_object_id": "uuid",
  "type": "references"
}
```

Rules are enforced by Application and Domain layers:

- both objects must exist in the requested organization;
- self-reference is rejected (`422`);
- duplicate directed relations are rejected (`409`);
- reverse directed relations remain valid.

Success: `201 Created` with `Location: /api/v1/relations/{id}`.

---

## Get and Delete Relation

```http
GET /api/v1/relations/{relation_id}
DELETE /api/v1/relations/{relation_id}
```

Delete performs a **hard delete** of the relation row only. Knowledge Objects are not deleted.

Repeated delete returns `404`.

---

## Traversal

### Outgoing / Incoming

Optional query parameter:

```text
type=<relation-type>
```

Returns an immutable `items` collection. Empty when no matches exist.

### Connected Knowledge Objects

Query parameters:

```text
direction=outgoing|incoming|both
type=<optional-relation-type>
```

When `direction` is omitted, the Application default is `outgoing`.

Connected-object results reuse the Knowledge Object response mapper. Deleted connected
objects are excluded. The starting object is not included in results.

---

## Deleted Knowledge Objects

- Traversal from a deleted starting object is rejected (`409` invalid state transition).
- Relations connected to deleted objects remain stored.
- Connected-object traversal excludes deleted endpoints.

Knowledge Object soft delete does **not** automatically delete relations.

---

## Transaction Ownership

Create and delete command handlers call `unit_of_work.commit()`.

Query handlers do not commit. The FastAPI Unit of Work dependency never adds an extra commit.

---

## Error Format

See [APIFoundation.md](APIFoundation.md) and [KnowledgeObjectAPI.md](KnowledgeObjectAPI.md).

See also [APIFoundation.md](APIFoundation.md) for dependency override strategy.
