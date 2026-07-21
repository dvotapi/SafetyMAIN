# Admin User API

Status: Active  
Date: 2026-07-21  
Task: TASK-P5-001

Related documents:

- [UserManagement.md](../architecture/UserManagement.md)
- [RoleBasedAuthorization.md](../architecture/RoleBasedAuthorization.md)
- [AuthenticationAPI.md](AuthenticationAPI.md)
- [APIFoundation.md](APIFoundation.md)

---

## Overview

Administrative user management is exposed under `/api/v1/admin/users`. All endpoints
require Bearer authentication, organization membership context (`X-Organization-ID`),
and RBAC permissions evaluated through `require_permission()`.

Users are global platform identities — list and lookup operations are not filtered
by organization.

---

## Endpoints

| Method | Path | Operation ID | Permission |
|--------|------|--------------|------------|
| `POST` | `/api/v1/admin/users` | `create_user` | `user:write` |
| `GET` | `/api/v1/admin/users` | `list_users` | `user:read` |
| `GET` | `/api/v1/admin/users/{user_id}` | `get_user` | `user:read` |
| `PATCH` | `/api/v1/admin/users/{user_id}` | `update_user` | `user:write` |
| `POST` | `/api/v1/admin/users/{user_id}/activate` | `activate_user` | `user:write` |
| `POST` | `/api/v1/admin/users/{user_id}/deactivate` | `deactivate_user` | `user:write` |

---

## User Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "operator@example.com",
  "display_name": "Operator",
  "is_active": true,
  "created_at": "2026-07-21T10:00:00Z",
  "updated_at": "2026-07-21T10:00:00Z"
}
```

Password hashes and internal persistence metadata are never included.

---

## Create User

### Request

```json
{
  "email": "operator@example.com",
  "display_name": "Operator",
  "is_active": true
}
```

`is_active` is optional and defaults to `true`.

### Errors

| HTTP | Code | Meaning |
|------|------|---------|
| `409` | `duplicate_user_email` | Email already registered |
| `422` | `request_validation_error` | Invalid email or empty required fields |
| `403` | `permission_denied` | Missing `user:write` |

---

## List Users

Query parameters:

| Parameter | Description |
|-----------|-------------|
| `page` | Page number (default `1`) |
| `page_size` | Items per page (default `20`, max `100`) |
| `sort` | `created_at` or `-created_at` |
| `email` | Case-insensitive substring filter |
| `display_name` | Case-insensitive substring filter |
| `is_active` | Filter by active state |

Response includes `items`, `page`, `page_size`, and `total`.

---

## Update User

Partial update via `PATCH`. At least one of `email`, `display_name`, or `is_active`
must be supplied.

---

## Lifecycle

- `POST .../activate` — transitions a deactivated user to active
- `POST .../deactivate` — transitions an active user to deactivated

Duplicate transitions return `409` with `user_already_active` or
`user_already_deactivated`.

---

## Authorization Matrix

| Role | List/Get | Create/Update/Lifecycle |
|------|----------|-------------------------|
| admin | allowed | allowed |
| auditor | allowed | denied (`403`) |
| member | denied (`403`) | denied (`403`) |
| unauthenticated | denied (`401`) | denied (`401`) |

Unknown roles fail closed with `403 permission_denied`.
