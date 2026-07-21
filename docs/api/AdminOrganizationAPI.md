# Admin Organization API

Status: Active  
Date: 2026-07-21  
Task: TASK-P5-002

Related documents:

- [OrganizationManagement.md](../architecture/OrganizationManagement.md)
- [RoleBasedAuthorization.md](../architecture/RoleBasedAuthorization.md)
- [AdminUserAPI.md](AdminUserAPI.md)
- [APIFoundation.md](APIFoundation.md)

---

## Overview

Administrative organization management is exposed under
`/api/v1/admin/organizations`. All endpoints require Bearer authentication,
organization membership context (`X-Organization-ID`), and RBAC permissions
evaluated through `require_permission()`.

Organizations are global records. The authorization organization in request
headers does not restrict which organizations an authorized administrator may
inspect or manage.

---

## Endpoints

| Method | Path | Operation ID | Permission |
|--------|------|--------------|------------|
| `POST` | `/api/v1/admin/organizations` | `create_organization` | `organization:write` |
| `GET` | `/api/v1/admin/organizations` | `list_organizations` | `organization:read` |
| `GET` | `/api/v1/admin/organizations/{organization_id}` | `get_organization` | `organization:read` |
| `PATCH` | `/api/v1/admin/organizations/{organization_id}` | `update_organization` | `organization:write` |
| `POST` | `/api/v1/admin/organizations/{organization_id}/activate` | `activate_organization` | `organization:write` |
| `POST` | `/api/v1/admin/organizations/{organization_id}/deactivate` | `deactivate_organization` | `organization:write` |

---

## Organization Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "SafetyMAIN Development Organization",
  "is_active": true,
  "created_at": "2026-07-21T10:00:00Z",
  "updated_at": "2026-07-21T10:00:00Z"
}
```

---

## Create Organization

### Request

```json
{
  "name": "SafetyMAIN Development Organization",
  "is_active": true
}
```

`is_active` is optional and defaults to `true`.

### Errors

| HTTP | Code | Meaning |
|------|------|---------|
| `409` | `duplicate_organization_name` | Normalized name already exists |
| `422` | `request_validation_error` | Empty or invalid name |
| `403` | `permission_denied` | Missing `organization:write` |

---

## List Organizations

Query parameters:

| Parameter | Description |
|-----------|-------------|
| `offset` | Result offset (default `0`) |
| `limit` | Page size (default `50`, max `100`) |
| `sort_asc` | Sort by `created_at` ascending when `true` |
| `name` | Case-insensitive substring filter |
| `is_active` | Filter by active state |

---

## Update Organization

`PATCH` accepts:

```json
{
  "name": "Renamed Organization"
}
```

Lifecycle changes use dedicated activate/deactivate endpoints.

---

## Lifecycle Conflicts

| Operation | Conflict code |
|-----------|---------------|
| Activate active organization | `organization_already_active` |
| Deactivate inactive organization | `organization_already_inactive` |
| Deactivate authorization organization | `current_organization_deactivation` |

---

## Authorization Matrix

| Role | List/Get | Create/Update/Lifecycle |
|------|----------|-------------------------|
| admin | allowed | allowed |
| auditor | allowed | denied (`403`) |
| member | denied (`403`) | denied (`403`) |
| unauthenticated | denied (`401`) | denied (`401`) |

Unknown roles fail closed with `403 permission_denied`.
