# Admin Audit API

Status: Active  
Date: 2026-07-23  
Task: TASK-P5-005, TASK-P6-001

Related documents:

- [AdministrativeAuditLog.md](../architecture/AdministrativeAuditLog.md)
- [AuditEventIntegrity.md](../architecture/AuditEventIntegrity.md)
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
| `GET` | `/integrity` | `verify_audit_chain_integrity` | `audit:read` |
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

All supplied filters use logical **AND** and exact matching.

| Parameter | Description |
|-----------|-------------|
| `event_name` | Canonical taxonomy event name (registry-validated; unknown → 422) |
| `event_category` | Taxonomy category (`ADMINISTRATIVE`, `AUTHENTICATION`, `AUTHORIZATION`, `SECURITY_INFRASTRUCTURE`) |
| `severity` | Registry significance (`INFORMATIONAL`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) |
| `action` | Stable audit action |
| `resource_type` | `USER`, `ORGANIZATION`, `MEMBERSHIP`, `INVITATION`, `AUDIT_EVENT`, `SESSION` |
| `resource_id` | Resource UUID |
| `actor_user_id` | Actor UUID |
| `request_id` | Exact request correlation ID from event metadata |
| `outcome` | `SUCCESS` or `FAILURE` |
| `target_organization_id` | Target organization UUID within allowed scope |
| `occurred_from` | Inclusive lower bound (timezone-aware) |
| `occurred_to` | Exclusive upper bound (timezone-aware) |
| `offset` | Pagination offset (default `0`) |
| `limit` | Page size (default `20`, max `100`) |
| `sort_ascending` | Sort by `occurred_at` ascending when `true` (default descending) |

Default sort: `occurred_at` descending, then event ID descending.

See [SecurityEventInvestigation.md](../architecture/SecurityEventInvestigation.md).

---

## Response Schema

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "actor_user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "authorization_organization_id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
  "target_organization_id": null,
  "event_name": "user.create",
  "event_category": "ADMINISTRATIVE",
  "severity": null,
  "action": "user.create",
  "resource_type": "USER",
  "resource_id": "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
  "outcome": "SUCCESS",
  "failure_code": null,
  "request_id": null,
  "metadata": {},
  "occurred_at": "2026-07-21T10:00:00Z",
  "previous_integrity_hash": null,
  "integrity_hash": "4afd7661af4418fac01ba20d02d987df6bdbcb106af20c32d28f56112fd314a7",
  "integrity_version": 1
}
```

Integrity verification:

```http
GET /api/v1/admin/audit-events/integrity
Authorization: Bearer <token>
X-Organization-ID: <organization-id>
```

See [AuditEventIntegrity.md](../architecture/AuditEventIntegrity.md).

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
