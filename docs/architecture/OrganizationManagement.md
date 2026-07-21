# Organization Management

Status: Active  
Date: 2026-07-21  
Task: TASK-P5-002

Related documents:

- [IdentityPersistence.md](IdentityPersistence.md)
- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)
- [UserManagement.md](UserManagement.md)

---

## 1. Organization Model

Organizations are global identity records with:

- public UUID identifier;
- trimmed display name (max 255 characters);
- active or deactivated lifecycle state;
- `created_at` and `updated_at` timestamps.

Memberships, users, Knowledge Objects, and Relations are not embedded in the
administration API responses.

---

## 2. Global Identity Scope

Organization administration operates on global records. List and lookup endpoints
do not restrict results to the authorization organization selected in the request
context.

---

## 3. Authorization Organization vs Target Organization

Protected requests still require:

- a valid Bearer access token;
- resolvable organization context (`X-Organization-ID`);
- active membership in the authorization organization;
- the required organization-management permission.

The **authorization organization** determines the caller's role and permissions.

The **target organization** is the global record being administered through path
parameters such as `/{organization_id}`.

These identifiers must remain distinct. Target organization IDs must not be treated
as implicit tenant context for authorization.

---

## 4. Lifecycle

Supported states:

- `ACTIVE`
- `DEACTIVATED`

Operations:

- create (active by default);
- update name;
- activate;
- deactivate.

Physical deletion is not exposed. Lifecycle operations do not mutate memberships.

Repeated activate/deactivate operations return stable `409` conflict errors.

---

## 5. Name Normalization and Uniqueness

Policy:

- trim leading and trailing whitespace;
- reject empty or whitespace-only names;
- enforce maximum length of 255 characters;
- compare duplicate names case-insensitively after normalization;
- preserve the trimmed display form in API responses.

Duplicate normalized names return `409 duplicate_organization_name`.

Database migration `0003_organization_active_state` adds a unique index on
`lower(name)`.

---

## 6. Permissions

| Permission | Value |
|------------|-------|
| Read | `organization:read` |
| Write | `organization:write` |

Role mapping:

| Role | read | write |
|------|------|-------|
| admin | yes | yes |
| auditor | yes | no |
| member | no | no |
| unknown | fail closed |

Policy constants: `ORGANIZATION_READ`, `ORGANIZATION_WRITE` in
`resource_permissions.py`.

---

## 7. API Operations

Prefix: `/api/v1/admin/organizations`

See [AdminOrganizationAPI.md](../api/AdminOrganizationAPI.md).

---

## 8. Pagination and Filtering

List endpoint supports:

- `offset` and `limit`;
- optional `is_active` filter;
- optional case-insensitive `name` substring filter;
- `sort_asc` for creation timestamp ordering.

Default ordering: `created_at` descending, `id` ascending as tiebreaker.

---

## 9. Error Semantics

| Situation | HTTP | Code |
|-----------|------|------|
| Organization not found | 404 | `organization_not_found` |
| Duplicate normalized name | 409 | `duplicate_organization_name` |
| Already active | 409 | `organization_already_active` |
| Already inactive | 409 | `organization_already_inactive` |
| Self-deactivation | 409 | `current_organization_deactivation` |
| Missing permission | 403 | `permission_denied` |
| Missing authentication | 401 | `unauthenticated` |

---

## 10. Self-Deactivation Protection

Deactivating the organization used as the current authorization context is rejected
with `409 current_organization_deactivation`.

This prevents an administrator from invalidating the active request context through
a single deactivate call.

---

## 11. Persistence

Repository contract extensions:

- `get_by_normalized_name`
- `list_organizations`

Alembic revision `0003_organization_active_state` adds `organizations.is_active` and
a unique normalized-name index.

---

## 12. Known Limitations

- Membership administration remains out of scope.
- Organization settings, billing, ownership, and deletion are not supported.
- Business-route lifecycle enforcement for inactive organizations is unchanged.
