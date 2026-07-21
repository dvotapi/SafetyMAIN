# Tenant Context Migration

Status: Active  
Date: 2026-07-21  
Task: TASK-P3-005

Related documents:

- [AuthenticationArchitecture.md](AuthenticationArchitecture.md)
- [AuthorizationFoundation.md](AuthorizationFoundation.md)

---

## 1. Purpose

P3-005 connects authenticated identity and organization membership to existing
Knowledge Object and Relation APIs through a resolved `TenantContext`.

Business handler logic remains unchanged. Organization isolation and cross-org
`404` masking are preserved.

---

## 2. Compatibility Mode

Controlled by `AUTH_ENFORCEMENT`:

| Value | Behavior |
|-------|----------|
| `false` (default) | Header-only tenant context; no Bearer auth; no membership checks |
| `true` | Bearer auth required; tenant resolution; active membership enforced |

Optional default tenant:

| Variable | Purpose |
|----------|---------|
| `DEFAULT_ORGANIZATION_ID` | Fallback organization when token/header do not select a tenant |

---

## 3. Tenant Resolution Flow

When `AUTH_ENFORCEMENT=true`:

```text
Bearer token validated
    ↓
Access token claims (sub, optional org_id)
    ↓
TenantContextResolver
    1. token org_id claim
    2. X-Organization-ID header
    3. DEFAULT_ORGANIZATION_ID
    4. single active membership auto-select
    ↓
AuthorizationService.require_organization_access()
    ↓
TenantContext returned to router
```

When token and header both provide an organization, they **must match** or the
API returns `422 organization_context_required`.

When `AUTH_ENFORCEMENT=false`:

```text
X-Organization-ID required
    ↓
Anonymous SecurityContext
    ↓
TenantContext with header organization only
```

---

## 4. API Integration

Business routers depend on `get_tenant_context()` instead of parsing the header
directly. Commands and queries continue to receive `organization_id` from the
resolved tenant context.

Authentication endpoints and system routes are unchanged.

---

## 5. SecurityContext in Application

`TenantContext` pairs:

- `security_context` — actor identity and authentication state;
- `organization_id` — resolved tenant boundary.

Handlers can access `tenant_context.actor_user_id` when audit fields are added
in later tasks.

---

## 6. Error Mapping

| Condition | HTTP | Code |
|-----------|------|------|
| Missing/invalid Bearer (enforced mode) | `401` | `unauthenticated` |
| Not an active member | `403` | `organization_access_denied` |
| Missing/ambiguous tenant selection | `422` | `organization_context_required` |
| Conflicting token/header organization | `422` | `organization_context_required` |
| Cross-org resource access | `404` | existing KO/relation codes |

---

## 7. Next Step

RBAC was introduced in P3-006. See [RoleBasedAuthorization.md](RoleBasedAuthorization.md).

**P3-007 — Security Architecture Review** is the next milestone.
