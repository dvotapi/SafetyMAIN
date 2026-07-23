# Admin Audit API

Status: Active  
Date: 2026-07-23  
Task: TASK-P5-005, TASK-P6-001

Related documents:

- [AdministrativeAuditLog.md](../architecture/AdministrativeAuditLog.md)
- [RoleBasedAuthorization.md](../architecture/RoleBasedAuthorization.md)
- [APIFoundation.md](APIFoundation.md)

---

## Overview

Administrative audit events are exposed read-only at:

```text
/api/v1/admin/audit-events
```

Audit events are produced only by trusted application workflows. There are no create,
update, or delete endpoints.

---

## Endpoints

| Method | Path | Operation ID | Permission |
|--------|------|--------------|------------|
| `GET` | `/` | `list_audit_events` | `audit:read` |
| `GET` | `/{audit_event_id}` | `get_audit_event` | `audit:read` |

---

## Authorization

Requires Bearer authentication, `X-Organization-ID`, and `audit:read`.

| Role | Read |
|------|-----:|
| admin | yes |
| auditor | yes |
| member | no |
| unknown | no |

There is no `audit:write` permission.

---

## Query Scoping

Results include events where either:

- `authorization_organization_id` equals the current organization; or
- `target_organization_id` equals the current organization.

Cross-organization event access returns `404`.

---

## List Filters

| Parameter | Description |
|-----------|-------------|
| `action` | Stable audit action |
| `resource_type` | `USER`, `ORGANIZATION`, `MEMBERSHIP`, `INVITATION`, `AUDIT_EVENT` |
| `resource_id` | Resource UUID |
| `actor_user_id` | Actor UUID |
| `outcome` | `SUCCESS` or `FAILURE` |
| `target_organization_id` | Target organization UUID within allowed scope |
| `occurred_from` | Inclusive lower bound |
| `occurred_to` | Inclusive upper bound |
| `offset` | Pagination offset (default `0`) |
| `limit` | Page size (default `20`, max `100`) |
| `sort_ascending` | Sort by `occurred_at` ascending when `true` (default descending) |

Default sort: `occurred_at` descending, then event ID.

---

## Response Schema

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "actor_user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "authorization_organization_id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
  "target_organization_id": null,
  "action": "user.create",
  "resource_type": "USER",
  "resource_id": "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
  "outcome": "SUCCESS",
  "failure_code": null,
  "metadata": {},
  "occurred_at": "2026-07-21T10:00:00Z"
}
```

Responses do not embed User, Organization, Membership, or Invitation DTOs.

---

## Error Semantics

| Situation | Status | Code |
|-----------|--------|------|
| Missing or invalid token | `401` | authentication codes |
| Missing `audit:read` | `403` | `permission_denied` (creates `authorization.permission_denied` audit event when actor and tenant context exist) |
| Event not found in scope | `404` | `audit_event_not_found` |
| Invalid filters | `422` | validation error envelope |

---

## Examples

List recent success events:

```http
GET /api/v1/admin/audit-events?outcome=SUCCESS&limit=20
Authorization: Bearer <token>
X-Organization-ID: <organization-id>
```

Get one event:

```http
GET /api/v1/admin/audit-events/<audit-event-id>
Authorization: Bearer <token>
X-Organization-ID: <organization-id>
```
