# Role-Based Authorization

Status: Active  
Date: 2026-07-23  
Task: TASK-P3-006, TASK-P6-001

Related documents:

- [AuthorizationFoundation.md](AuthorizationFoundation.md)
- [TenantContextMigration.md](TenantContextMigration.md)
- [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md)
- [IdentityDomain.md](IdentityDomain.md)

---

## 1. Purpose

This document describes role-based authorization (RBAC) introduced in P3-006.
Authorization decisions extend the P3-004 membership foundation with role and
permission evaluation.

Tenant isolation, membership validation, and handler business logic remain
unchanged. Business routes apply permission checks through `require_permission()`
(P4-002).

---

## 2. RBAC Model

RBAC uses the domain role model from P3-002:

| System role | Purpose |
|-------------|---------|
| `admin` | Full organization capabilities |
| `member` | Read/write Knowledge Objects and manage Relations |
| `auditor` | Read-only Knowledge Object access |

Permissions are defined in `backend/core/domain/value_objects/permission.py` and
mapped to roles in `backend/core/domain/value_objects/role_permissions.py`.

The Application layer does not redefine permissions. `RolePermissionResolver`
delegates to `permissions_for_role()`.

---

## 3. Authorization Flow

```text
TenantContext (API)
    ↓
AuthorizationService.require_permission()
    ↓
OrganizationAccessPolicy (membership — unchanged)
    ↓
PermissionAccessPolicy
    ↓
PermissionEvaluator
    ↓
MembershipLookupPort.get_membership() → role
    ↓
RolePermissionResolver → permissions_for_role()
    ↓
PermissionDeniedError when capability is missing
```

Membership verification remains the first authorization step. Permission
evaluation runs only after active membership is confirmed.

---

## 4. Role Resolution

`PermissionEvaluator.resolve_role()` loads the active `Membership` for the
actor and organization, then reads `membership.role`.

Supported roles:

- `Role.admin()`
- `Role.member()`
- `Role.auditor()`

Custom role strings outside the system enum are rejected by the domain resolver.

---

## 5. Permission Evaluation

### Components

| Component | Layer | Responsibility |
|-----------|-------|----------------|
| `RolePermissionResolver` | Application | Resolve permissions for a role |
| `PermissionEvaluator` | Application | Evaluate membership role against a required permission |
| `PermissionAccessPolicy` | Application | Reusable policy wrapper around the evaluator |
| `AuthorizationService` | Application | Orchestrate membership + permission checks |

All components depend on contracts and domain types only. They do not import
FastAPI, JWT, or Infrastructure.

### Reusable resource policies

`backend/core/application/authorization/policies/resource_permissions.py`
defines reusable policy constants:

| Policy constant | Required domain permission |
|-----------------|----------------------------|
| `KNOWLEDGE_OBJECT_READ` | `knowledge_object:read` |
| `KNOWLEDGE_OBJECT_WRITE` | `knowledge_object:write` |
| `KNOWLEDGE_OBJECT_DELETE` | `knowledge_object:write` |
| `RELATION_READ` | `relation:manage` |
| `RELATION_WRITE` | `relation:manage` |
| `RELATION_DELETE` | `relation:manage` |
| `USER_READ` | `user:read` |
| `USER_WRITE` | `user:write` |
| `ORGANIZATION_READ` | `organization:read` |
| `ORGANIZATION_WRITE` | `organization:write` |
| `MEMBERSHIP_READ` | `membership:read` |
| `MEMBERSHIP_WRITE` | `membership:write` |
| `AUDIT_READ` | `audit:read` |

Admin user API permissions (P5-001):

| Role | `user:read` | `user:write` |
|------|-------------|--------------|
| admin | yes | yes |
| member | no | no |
| auditor | yes | no |

Admin organization API permissions (P5-002):

| Role | `organization:read` | `organization:write` |
|------|---------------------|----------------------|
| admin | yes | yes |
| member | no | no |
| auditor | yes | no |

Admin membership API permissions (P5-003):

| Role | `membership:read` | `membership:write` |
|------|-------------------|---------------------|
| admin | yes | yes |
| member | no | no |
| auditor | yes | no |

Admin audit API permissions (P5-005):

| Role | `audit:read` |
|------|--------------|
| admin | yes |
| auditor | yes |
| member | no |

There is no public `audit:write` permission. Audit writes are internal application behavior.

Relation and delete policies map to existing domain capabilities because P3-002
defines `relation:manage` and does not split relation or delete permissions.

---

## 6. Authorization Service Extension

`AuthorizationService` adds:

| Method | Responsibility |
|--------|----------------|
| `require_permission()` | Verify membership, then evaluate role permissions |

Existing methods are unchanged:

- `require_organization_access()`
- `authorize_security_context()`

---

## 7. API Integration

Permission checks are exposed as a FastAPI dependency:

```python
tenant_context: Annotated[
    TenantContext,
    Depends(require_permission(KNOWLEDGE_OBJECT_WRITE)),
]
```

Behavior:

- `AUTH_ENFORCEMENT=false` — dependency is a no-op (compatibility mode)
- `AUTH_ENFORCEMENT=true` — membership and permission checks run

Knowledge Object and Relation routers apply `require_permission()` to every
business endpoint (P4-002). See
[SecurityEnforcementRollout.md](SecurityEnforcementRollout.md) for the full
permission matrix.

---

## 8. Error Mapping

| Exception | HTTP | Public code |
|-----------|------|-------------|
| `PermissionDeniedError` | 403 | `permission_denied` |
| `OrganizationAccessDeniedError` | 403 | `organization_access_denied` |

`PermissionDeniedError` indicates an authenticated member without the required
capability. `OrganizationAccessDeniedError` indicates missing or inactive
membership.

When `AUTH_ENFORCEMENT=true` and the denied permission is an administrative system
permission (`user:*`, `organization:*`, `membership:*`, `invitation:*`, `audit:read`),
`require_permission()` records one `authorization.permission_denied` audit event if
trusted actor and `TenantContext` were resolved before evaluation. Business permission
denials are not written to the administrative audit log. Audit persistence failure does
not change the `403 permission_denied` HTTP response.

---

## 9. Migration State

| Milestone | Capability |
|-----------|------------|
| P3-004 | Membership enforcement |
| P3-005 | Tenant context migration |
| P3-006 | Role and permission evaluation |
| P3-007 | Security architecture review |
| P4-002 | Business route enforcement |
| P5-001 | User Management API |
| P5-002 | Organization Management API |
| P5-003 | Membership Management API (this rollout) |
| P6-001 | Administrative permission-denial auditing |
| P6-002 | Security Event Taxonomy & Registry |

See [UserManagement.md](UserManagement.md), [OrganizationManagement.md](OrganizationManagement.md),
and [MembershipManagement.md](MembershipManagement.md).

---

## 10. Non-Goals

This milestone does not:

- change the domain role or permission model;
- modify tenant resolution;
- add attribute-based access control;
- enforce permissions on existing handlers automatically.

Administrative audit read access (`audit:read`) is implemented in P5-005. Internal audit writes are not RBAC-granted permissions.

---

## 11. Phase P3 Review

Security architecture review completed in
[SecurityArchitectureReview.md](SecurityArchitectureReview.md).

**Decision: `READY WITH CONDITIONS`**
