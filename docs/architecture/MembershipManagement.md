# Membership Management

Status: Active  
Date: 2026-07-21  
Task: TASK-P5-003

Related documents:

- [OrganizationManagement.md](OrganizationManagement.md)
- [UserManagement.md](UserManagement.md)
- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)
- [IdentityPersistence.md](IdentityPersistence.md)

---

## 1. API Overview

Administrative membership management is exposed at:

```text
/api/v1/admin/memberships
```

Operations:

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| POST | `/` | `membership:write` | Create membership |
| GET | `/` | `membership:read` | List memberships |
| GET | `/{membership_id}` | `membership:read` | Get membership |
| PATCH | `/{membership_id}/role` | `membership:write` | Change role |
| POST | `/{membership_id}/activate` | `membership:write` | Activate membership |
| POST | `/{membership_id}/deactivate` | `membership:write` | Deactivate membership |

Membership administration is organization-scoped. List operations require a target
`organization_id` query parameter.

---

## 2. Authorization Organization vs Target Organization

Protected requests still require Bearer authentication and organization membership
context (`X-Organization-ID`).

- **Authorization organization** — resolved from `TenantContext`; determines RBAC
  permissions for the caller.
- **Target organization** — supplied in create/list requests or implied by the
  membership record being administered.

Permission evaluation uses the authorization organization. Membership mutations affect
records in the target organization only.

These identifiers must remain distinct.

---

## 3. Lifecycle

Supported states:

- `ACTIVE` — grants organization access
- `REVOKED` — inactive but queryable (admin deactivate maps here)
- `INVITED` — out of scope for admin create (create defaults to active)

Create accepts optional `is_active` (default `true`). Activate and deactivate are
separate endpoints. Repeated lifecycle operations return stable `409` conflicts.

Physical deletion is not supported.

---

## 4. Safety Rules (Application Layer)

Implemented in `backend/core/application/policies/membership_administration.py` and
enforced by Application handlers:

| Rule | Error code |
|------|------------|
| Self deactivation of authorization membership | `self_membership_deactivation` |
| Self role downgrade from admin | `self_membership_role_downgrade` |
| Removing last active administrator from target org | `last_organization_administrator` |

These checks live in Application use cases so they apply consistently regardless of
transport.

---

## 5. Permissions

| Permission | Value |
|------------|-------|
| Read | `membership:read` |
| Write | `membership:write` |

Role mapping:

| Role | read | write |
|------|------|-------|
| admin | yes | yes |
| auditor | yes | no |
| member | no | no |
| unknown | fail closed |

---

## 6. Validation

Create requires:

- existing user and organization;
- valid domain role (`admin`, `member`, `auditor`);
- no duplicate `(organization_id, user_id)` pair.

Invalid roles return `422 invalid_membership_role`.

---

## 7. Pagination and Filtering

List endpoint requires `organization_id` and supports:

- `user_id`, `role`, `is_active` filters;
- `offset`, `limit`, `sort_asc`;
- stable ordering: `created_at` descending, `id` ascending.

---

## 8. Error Semantics

| Situation | HTTP | Code |
|-----------|------|------|
| Membership not found | 404 | `membership_not_found` |
| User not found | 404 | `user_not_found` |
| Organization not found | 404 | `organization_not_found` |
| Duplicate membership | 409 | `duplicate_membership` |
| Self deactivation | 409 | `self_membership_deactivation` |
| Self role downgrade | 409 | `self_membership_role_downgrade` |
| Last administrator | 409 | `last_organization_administrator` |
| Invalid role | 422 | `invalid_membership_role` |

---

## 9. Known Limitations

- No invitation workflows
- No membership deletion
- No automatic user or organization provisioning

See [AdminMembershipAPI.md](../api/AdminMembershipAPI.md) for request/response examples.

Membership administrative mutations emit audit events (`membership.create`,
`membership.role_change`, `membership.activate`, `membership.deactivate`).
See [AdministrativeAuditLog.md](AdministrativeAuditLog.md).
