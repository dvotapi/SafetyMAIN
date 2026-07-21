# Authorization Foundation

Status: Active  
Date: 2026-07-21  
Task: TASK-P3-004

Related documents:

- [AuthenticationArchitecture.md](AuthenticationArchitecture.md)
- [IdentityDomain.md](IdentityDomain.md)
- [AuthenticationAPI.md](../api/AuthenticationAPI.md)
- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)

---

## 1. Purpose

This document describes the Application authorization foundation introduced in
P3-004. Authorization decisions are based on authenticated identity and active
organization membership.

Business endpoints remain unchanged in this milestone. Handlers can adopt the
authorization service in P3-005 without altering existing organization isolation
semantics for Knowledge Objects.

---

## 2. Authorization Flow

```text
SecurityContext (Application)
    ↓
AuthorizationService
    ↓
OrganizationAccessPolicy
    ↓
MembershipVerificationPort
    ↓
Infrastructure membership adapter
```

The API layer builds `SecurityContext` from Bearer authentication. Application
handlers remain JWT-independent and consume only Application types.

---

## 3. SecurityContext Integration

Canonical model: `backend/core/application/context/security_context.py`

| Field | Purpose |
|-------|---------|
| `is_authenticated` | Whether the request has a validated identity |
| `user_id` / `actor_user_id` | Authenticated platform user |
| `organization_id` | Selected tenant for the request |
| `authentication_method` | Transport hint for telemetry only |
| `request_id` | Correlation identifier |

Factory helpers:

- `SecurityContext.anonymous()` — unauthenticated requests
- `SecurityContext.authenticated()` — authenticated identity with optional tenant

The API module re-exports this model for FastAPI dependencies without placing
HTTP concerns inside Application services.

---

## 4. Authorization Service

`AuthorizationService` coordinates policy evaluation for handlers.

| Method | Responsibility |
|--------|----------------|
| `require_organization_access()` | Verify active membership for actor + organization |
| `require_permission()` | Verify membership, then evaluate role permissions (P3-006, applied P4-002) |
| `authorize_security_context()` | Validate authenticated tenant context before handler work |

Dependencies:

- `AuthorizationPolicyPort` (default: `OrganizationAccessPolicy`)
- `MembershipVerificationPort` (used by the default policy)
- `PermissionPolicyPort` (default: `PermissionAccessPolicy`, P3-006)

The service is wired in Bootstrap and exposed on `AppContainer.authorization_service`.

---

## 5. Policies

Organization access policy (P3-004):

| Policy | Decision |
|--------|----------|
| Authenticated user | `SecurityContext.is_authenticated` must be true |
| Active membership | `MembershipVerificationPort.is_active_member()` must be true |
| Organization access | Raises `OrganizationAccessDeniedError` when membership is absent or inactive |

Role- and permission-based policies were added in P3-006. See
[RoleBasedAuthorization.md](RoleBasedAuthorization.md).

---

## 6. Ports

| Port | Module | Purpose |
|------|--------|---------|
| `MembershipVerificationPort` | `contracts/membership_verification.py` | Active membership check |
| `MembershipLookupPort` | `contracts/membership_lookup.py` | Resolve memberships for tenant selection |
| `AuthorizationPolicyPort` | `contracts/authorization_policy.py` | Reusable authorization policy contract |
| `PermissionPolicyPort` | `contracts/permission_policy.py` | Permission policy contract (P3-006) |

`OrganizationMembershipVerificationPort` remains as a compatibility alias for
`MembershipVerificationPort`.

---

## 7. Authorization Exceptions

| Exception | HTTP | Public code |
|-----------|------|-------------|
| `OrganizationAccessDeniedError` | `403` | `organization_access_denied` |
| `PermissionDeniedError` | `403` | `permission_denied` |
| `MembershipRequiredError` | `422` | `organization_context_required` |

Exceptions are mapped through the existing API error envelope. Cross-organization
Knowledge Object access continues to return `404` through existing Application
validators — authorization failures for membership are distinct from resource
masking.

---

## 8. Infrastructure

`InMemoryMembershipStore` implements `MembershipLookupPort` and
`MembershipVerificationPort` for development and tests. SQLAlchemy adapters are
deferred to a later persistence task.

---

## 9. Next Step

**P3-007 — Security Architecture Review** follows RBAC introduction in
[RoleBasedAuthorization.md](RoleBasedAuthorization.md).

See [SecurityArchitectureReview.md](SecurityArchitectureReview.md) for the Phase P3
readiness decision.
