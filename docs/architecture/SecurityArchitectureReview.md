# Security Architecture Review

Status: Active  
Date: 2026-07-21  
Task: TASK-P3-007

Related documents:

- [AuthenticationArchitecture.md](AuthenticationArchitecture.md)
- [AuthorizationFoundation.md](AuthorizationFoundation.md)
- [TenantContextMigration.md](TenantContextMigration.md)
- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)
- [IdentityDomain.md](IdentityDomain.md)
- [ArchitectureReviewV2.md](ArchitectureReviewV2.md)
- [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md)

---

## 1. Executive Summary

Phase P3 introduced authentication, tenant context migration, membership
authorization, and role-based authorization while preserving the existing
organization isolation model for Knowledge Objects and Relations.

This review validated Clean Architecture boundaries, authentication and
authorization flows, compatibility mode behavior, error semantics, tenant
isolation, configuration risks, OpenAPI security definitions, and test coverage.

**Final decision: `READY WITH CONDITIONS`**

Phase P3 security functionality is architecturally sound and test-backed. Remaining
conditions are operational and rollout-related rather than blocking design defects.

---

## 2. Reviewed Scope

| Milestone | Scope |
|-----------|-------|
| P3-001 | Authentication and identity architecture |
| P3-002 | User and Organization domain model |
| P3-003 | Authentication API (login, refresh, JWT) |
| P3-004 | Authorization foundation (membership) |
| P3-005 | Tenant context migration and compatibility mode |
| P3-006 | Role-based authorization (opt-in) |

Review covered Application, Domain, Contracts, Infrastructure, API, Bootstrap,
tests, and architecture documentation.

---

## 3. Architecture Conformance

### Verified

- **Domain** does not import Application, Infrastructure, API, FastAPI, JWT, or
  SQLAlchemy.
- **Application** authorization and tenant modules do not import FastAPI, JWT,
  or concrete Infrastructure adapters.
- **API routers** delegate to Application handlers and do not construct
  authorization services or call repositories directly.
- **Infrastructure** implements Contracts (`TokenServiceContract`,
  `MembershipLookupPort`, `MembershipVerificationPort`, password hasher).
- **Bootstrap** owns composition in `AppContainer`.
- Authentication, tenant resolution, and authorization remain separated:
  - JWT validation → API dependencies
  - Tenant resolution → `TenantContextResolver`
  - Membership → `OrganizationAccessPolicy`
  - Permissions → `PermissionEvaluator` (opt-in)

### Architecture tests extended

`tests/architecture/test_security_boundaries.py` guards security-specific import
and router call boundaries in addition to existing layer tests.

---

## 4. Authentication Assessment

### Verified behavior

| Scenario | Result |
|----------|--------|
| Valid login | Issues access + refresh token pair |
| Invalid password | `401` / `invalid_credentials` |
| Unknown user | `401` / `invalid_credentials` (no user enumeration) |
| Inactive/suspended user | `403` / `authentication_forbidden` |
| Valid refresh | Rotates token pair |
| Access token used as refresh | Rejected |
| Refresh token used as access | Rejected |
| Expired access token | Rejected |
| Invalid signature | Rejected |
| Invalid issuer (when configured) | Rejected |
| Malformed Bearer on business route | `401` / `unauthenticated` |

### Review notes

- Raw JWT payloads remain in Infrastructure (`JwtTokenService`) and API
  dependencies. Application handlers consume `UserId`, `AccessTokenClaims`, and
  `SecurityContext` only.
- Password verification stays behind `PasswordHasherContract` and credential
  ports.
- **Hardening applied during review:** issuer claim validation when `JWT_ISSUER`
  is configured.

### Residual risks

- Default `JWT_SECRET_KEY` is development-only.
- HS256 symmetric signing is acceptable for MVP; asymmetric signing remains a
  future hardening option.

---

## 5. Tenant-Context Assessment

### Resolution priority (verified)

1. Token organization claim (`org_id`)
2. Compatible `X-Organization-ID` header
3. Configured `DEFAULT_ORGANIZATION_ID`
4. Sole active membership fallback

### Verified behavior

| Scenario | Result |
|----------|--------|
| Token org only | Resolved |
| Header fallback | Resolved |
| Matching token + header | Resolved |
| Conflicting token + header | `422` / `organization_context_required` |
| Default organization | Resolved |
| Sole active membership | Resolved |
| Multiple active memberships without selection | `422` |
| Missing organization context | `422` |

Handlers receive resolved `organization_id` from routers via `TenantContext`.
No business handler independently resolves tenant context.

---

## 6. Membership Authorization Assessment

### Verified

- Membership verification uses `MembershipVerificationPort`.
- Active membership is required when `AUTH_ENFORCEMENT=true`.
- Invited and revoked memberships are rejected with `403`.
- Membership authorization runs before permission evaluation.
- Repository-level organization filtering remains unchanged.
- Non-member organization selection returns `403`, not resource existence leaks.

---

## 7. RBAC Assessment

### Verified

- Roles resolve from active `Membership.role`.
- Role-to-permission mapping uses domain `permissions_for_role()`.
- `admin`, `member`, and `auditor` behave per domain policy.
- Unknown roles deny permissions safely (empty permission set).
- `PermissionDeniedError` maps to `403` / `permission_denied`.
- Permission checks require prior membership validation.
- `require_permission()` applied to all Knowledge Object and Relation business routes (P4-002).

### Compatibility mode

When `AUTH_ENFORCEMENT=false`, `require_permission()` is a documented no-op.

---

## 8. Tenant-Isolation Assessment

Cross-organization access remains masked as `404` at the Application and API
layers for:

- Knowledge Object reads, writes, lifecycle, history
- Relation operations and traversal
- Structured search

Verified under both compatibility mode and enforced authentication. When a user
is a member of multiple organizations, selecting a different organization context
does not reveal resources from another tenant.

Permission denial (`403`) is distinct from cross-organization masking (`404`).

---

## 9. Error-Semantics Assessment

| Situation | HTTP | Public code | Verified |
|-----------|------|-------------|----------|
| Missing/invalid authentication | 401 | `unauthenticated` | Yes |
| Invalid credentials | 401 | `invalid_credentials` | Yes |
| Invalid refresh token | 401 | `invalid_refresh_token` | Yes |
| Authentication forbidden | 403 | `authentication_forbidden` | Yes |
| Organization membership denied | 403 | `organization_access_denied` | Yes |
| Permission denied | 403 | `permission_denied` | Yes |
| Administrative permission denied (audit) | 403 | `permission_denied` | Yes (P6-001, scoped audit event when trusted context exists) |

Persisted security event type identity, category, subject domain, and producer ownership
for current audit records are centralized in [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md)
(TASK-P6-002). Runtime audit behavior is unchanged.

| Missing/ambiguous organization context | 422 | `organization_context_required` | Yes |
| Conflicting organization contexts | 422 | `organization_context_required` | Yes |
| Cross-organization resource access | 404 | domain codes | Yes |

All errors use the common API envelope. Responses do not expose token payloads,
passwords, or internal exception details.

---

## 10. Configuration Assessment

| Setting | Assessment |
|---------|------------|
| `JWT_SECRET_KEY` | Validated at startup; production rejects placeholders and short secrets |
| `JWT_ALGORITHM` | Whitelist enforced at startup (`HS256`, `HS384`, `HS512`) |
| `JWT_*_TTL_SECONDS` | Positive integer, documented ranges, refresh must exceed access |
| `JWT_ISSUER` | Validated on decode when configured; required in production |
| `AUTH_ENFORCEMENT` | Boolean parsing with explicit error on invalid values |
| `APP_ENV=production` | Requires strong secret, issuer, database URL, and enforcement |
| `DEFAULT_ORGANIZATION_ID` | UUID validation |

Compatibility mode (`AUTH_ENFORCEMENT=false`) is documented as transitional.
Secrets are not logged or returned in API responses.

---

## 11. OpenAPI Assessment

### Verified

- Authentication endpoints documented
- `BearerAuth` security scheme defined
- System routes exempt from organization header
- Business routes document `X-Organization-ID`
- Operation IDs remain stable

### Verified (P4-002 update)

- Business operations declare `security: [BearerAuth]` in OpenAPI (enforced contract)
- Protected operations document `401` and `403` responses

### Known limitation

OpenAPI describes the enforced-mode contract statically. When
`AUTH_ENFORCEMENT=false`, compatibility mode allows header-only access without
Bearer tokens even though OpenAPI documents Bearer requirements. See
[SecurityEnforcementRollout.md](SecurityEnforcementRollout.md).

---

## 12. Test Coverage Assessment

Consolidated security matrix: `tests/security/test_security_matrix.py`

Coverage includes authentication, tenant context, membership, RBAC, isolation,
and compatibility mode scenarios. Existing suites remain authoritative for domain,
API contract, and PostgreSQL tests.

**Validation results (review run):**

- `398 passed`, `64 skipped`
- Ruff clean
- Architecture tests pass (including new security boundary tests)

Database-marked tests skipped when PostgreSQL is unavailable (expected).

---

## 13. Known Limitations

1. **In-memory identity and membership stores** — development/test adapters only.
2. **Compatibility mode default** — `AUTH_ENFORCEMENT=false` preserves legacy
   header-only clients.
3. **OpenAPI describes enforced contract statically** — see SecurityEnforcementRollout.md.
4. **Production configuration must be set explicitly** — startup validation rejects unsafe production settings (P4-003).
5. **HS256 dev secret default** — not production-safe without configuration.
6. **No audit logging** — out of Phase P3 scope.
7. **No OIDC / external IdP** — future adapter track.

---

## 14. Required Follow-Up Work

| Priority | Task |
|----------|------|
| High | Persist identity and membership (SQLAlchemy adapters) |
| High | Deploy with validated production security configuration (P4-003) |
| Medium | Enable `AUTH_ENFORCEMENT=true` in production after client migration |
| Low | Retire compatibility mode when all clients use Bearer tokens |
| Low | Evaluate asymmetric JWT signing (RS256/EdDSA) |
| Low | Add JWT algorithm whitelist in settings if additional algorithms are never required |
| Future | OIDC / enterprise IdP adapter (post Phase P3 closeout) |

---

## 15. Final Readiness Decision

```text
READY WITH CONDITIONS
```

Phase P3 security implementation conforms to SafetyMAIN architecture, preserves
tenant isolation, and provides a complete authentication and authorization
foundation. The conditions in §14 must be tracked during the next project phase
but do not block closing Phase P3.

---

## SecurityContext Invariants

The following invariants must be preserved:

1. `SecurityContext` is owned by the Application layer.
2. `anonymous()` → `is_authenticated=false`, `user_id=None`.
3. `authenticated()` → `is_authenticated=true`, `user_id` required.
4. `actor_user_id` is `None` for anonymous contexts.
5. API re-exports must not introduce duplicate security models.
6. Organization context on `SecurityContext` is optional until tenant resolution
   completes.

---

## Temporary Adapters (Bootstrap)

| Adapter | Replacement target |
|---------|-------------------|
| `InMemoryIdentityStore` | SQLAlchemy user/credential repository |
| `InMemoryMembershipStore` | SQLAlchemy membership repository |

Both implement the correct Contracts ports and are wired explicitly in
`AppContainer`.
