# User Management

Status: Active  
Date: 2026-07-21  
Task: TASK-P5-001

Related documents:

- [IdentityPersistence.md](IdentityPersistence.md)
- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)
- [SecurityEnforcementRollout.md](SecurityEnforcementRollout.md)

---

## 1. API Overview

Administrative user management is exposed at:

```text
/api/v1/admin/users
```

Operations:

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| POST | `/` | `user:write` | Create user |
| GET | `/` | `user:read` | List users |
| GET | `/{user_id}` | `user:read` | Get user |
| PATCH | `/{user_id}` | `user:write` | Update user |
| POST | `/{user_id}/activate` | `user:write` | Activate user |
| POST | `/{user_id}/deactivate` | `user:write` | Deactivate user |

Users are global platform identities. List and lookup operations are not filtered by
organization. Authorization still uses the existing Bearer token, organization
membership context, and RBAC evaluation through `require_permission()`.

Password hashes and internal persistence details are never returned in API
responses.

---

## 2. Lifecycle

Supported states:

- `ACTIVE` — user can authenticate when a password is configured
- `DEACTIVATED` — user cannot authenticate

Create accepts an optional `is_active` flag (default `true`). Activate and
deactivate endpoints transition between active and deactivated states and reject
duplicate transitions with `409`.

Password management, invitations, and email verification are out of scope for this
task.

---

## 3. Permissions

Domain permissions:

| Permission | Value |
|------------|-------|
| Read | `user:read` |
| Write | `user:write` |

Role mapping:

| Role | Access |
|------|--------|
| admin | read + write |
| member | none |
| auditor | read only |
| unknown | fail closed |

Policy constants: `USER_READ`, `USER_WRITE` in
`backend/core/application/authorization/policies/resource_permissions.py`.

---

## 4. Validation

Create:

- email format and non-empty value;
- display name non-empty;
- optional active flag.

Update:

- optional email, display name, and active flag;
- duplicate email rejected with `409 duplicate_user_email`.

Invalid UUID path parameters return `422` through existing FastAPI validation.

---

## 5. Pagination and Filtering

List endpoint supports:

- `offset` (default `0`);
- `limit` (default `50`, max `100`);
- `is_active`;
- `email` substring filter;
- `display_name` substring filter;
- `sort_asc` boolean for created-at ordering (default descending).

---

## 6. Error Model

| Situation | HTTP | Code |
|-----------|------|------|
| Validation failure | 422 | `request_validation_error` |
| Unauthenticated | 401 | `unauthenticated` |
| Missing permission | 403 | `permission_denied` |
| User not found | 404 | `user_not_found` |
| Duplicate email | 409 | `duplicate_user_email` |
| Already active / deactivated | 409 | `user_already_active` / `user_already_deactivated` |

---

## 7. Extension Points

Future work can add:

- password reset and credential provisioning hooks;
- organization and membership administration APIs;
- suspended-state persistence separate from deactivated;
- audit logging for administrative actions.

Application handlers remain framework-free and use `UserRepositoryContract` through
Unit of Work.

---

## 8. Implementation Status

| Area | Status |
|------|--------|
| Application use cases | Implemented |
| Admin router | Implemented |
| RBAC permissions | Implemented |
| OpenAPI operation IDs | Implemented |
| Repository list/filter | Implemented |
| Tests | Application, API, repository contracts |

Authentication behavior, tenant isolation for business APIs, and existing JWT
format remain unchanged.
