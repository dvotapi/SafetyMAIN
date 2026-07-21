# Identity and Authentication Architecture

Status: Active  
Date: 2026-07-20  
Task: TASK-P3-001

Related documents:

- [ArchitectureConstitution.md](ArchitectureConstitution.md) — Article VIII (Organization Is the Boundary)
- [ArchitectureReviewV2.md](ArchitectureReviewV2.md) — readiness gate for authentication foundation
- [APIFoundation.md](../api/APIFoundation.md) — request ID and error envelope
- [ArchitectureTesting.md](ArchitectureTesting.md) — dependency rules

---

## 1. Purpose

This document defines how authenticated users, organizations, tenant context, and
authorization boundaries integrate into SafetyMAIN **without changing current runtime
behavior**.

TASK-P3-001 is **architecture-only**. It establishes the blueprint for subsequent
implementation tasks beginning with **P3-002 — User and Organization Domain**.

### In scope

- Identity model and security context
- Authentication flow and FastAPI integration points
- Tenant context replacing blind trust in `X-Organization-ID`
- Authorization boundary placement across layers
- Future domain concepts (User, membership, roles, permissions)
- Migration strategy from the temporary organization header

### Out of scope (this task)

- Token issuance, login endpoints, user registration
- Database tables, repositories, or migrations
- Changes to Application handlers, API routes, or OpenAPI
- Fine-grained RBAC enforcement
- Active Directory / SSO integration implementation

---

## 2. Current State (Baseline)

### Temporary tenant transport

Business HTTP requests require:

```text
X-Organization-ID: <uuid>
```

Implemented in:

- `backend/api/dependencies.py` — `get_organization_id()`
- `backend/api/knowledge_object_params.py` — header constant

Behavior today:

- any syntactically valid UUID is accepted;
- **no caller identity** is established;
- **no membership check** verifies the caller belongs to the organization;
- system routes (`/health`, `/ready`) do not require organization context.

### Organization isolation (unchanged by this design)

Application handlers enforce organization boundaries through:

- `organization_id` on every Command and Query;
- `validate_knowledge_object_organization()` and related helpers in Application;
- repository search and relation queries scoped by `OrganizationId`;
- cross-organization object access masked as `404 Not Found` (not `403`).

The authentication architecture **must preserve these semantics** for Knowledge Object
and Relation access patterns.

### Constitutional anchor

From Architecture Constitution, Article VIII:

> Every Knowledge Object belongs to an Organization.  
> Organization defines ownership, security and responsibility.

Organization remains the **primary tenant and security boundary**.

---

## 3. Identity Model

### 3.1 Authenticated user

An **authenticated user** is a platform identity that has successfully proved
credentials at the HTTP boundary.

Conceptual attributes (future Domain / read models):

| Concept | Description |
|---------|-------------|
| **User** | Human or service identity with stable platform ID |
| **UserId** | Immutable identifier (value object) |
| **Authentication status** | Proved at request boundary; not re-validated in Domain |
| **Subject** | External identity reference (e.g. OIDC `sub`) when federated |

The authenticated user is represented in Application as a **security principal**, not
as a FastAPI or JWT type.

### 3.2 Anonymous request

An **anonymous request** has no valid authentication credentials.

Rules:

| Route class | Anonymous access |
|-------------|------------------|
| System (`/health`, `/ready`) | Allowed |
| Business API | Rejected with `401 Unauthorized` (future) |
| Documentation / OpenAPI | Allowed (static) |

Anonymous requests must **not** carry effective tenant authority. Any organization
context derived without authentication is invalid for business routes.

### 3.3 Identity lifecycle (conceptual)

```text
Provisioned → Active → Suspended → Deactivated
```

Lifecycle transitions are out of scope for P3-002 implementation details, but the
architecture reserves:

- membership revocation independent of user deactivation;
- suspended users fail authentication before authorization;
- deactivated users cannot obtain new sessions.

### 3.4 Authentication boundary

The **authentication boundary** is the HTTP ingress plus Bootstrap composition:

```text
HTTP Request
    ↓
Authentication middleware / dependency  (API + Bootstrap)
    ↓
SecurityContext (Application-facing, transport-free)
    ↓
Command / Query construction            (API)
    ↓
Application handler                     (membership + existing org rules)
```

Everything above Application that parses tokens, headers, or cookies belongs to
**API** or **Bootstrap**. Application receives already-authenticated context through
explicit Command/Query fields or a dedicated Application port — never through
FastAPI imports.

### 3.5 Security context

**SecurityContext** (future Application or API-adjacent immutable object) carries:

```text
SecurityContext
├── user_id: UserId | None          # None only for explicitly public routes
├── organization_id: OrganizationId # Resolved tenant for this request
├── authentication_method: str    # e.g. bearer_jwt, api_key (telemetry only)
└── request_id: str               # Correlation; mirrors X-Request-ID
```

Properties:

- immutable for the lifetime of one HTTP request;
- created once at the inbound edge;
- passed into Command/Query construction;
- never stored in Domain entities as a service locator.

---

## 4. Tenant Context

### 4.1 Problem with the current header

`X-Organization-ID` is a **transport hint**, not proof of tenant authority. Any client
can supply any UUID. Authentication requires **verified tenant context**.

### 4.2 Target tenant context

**Tenant context** is the combination of:

1. authenticated **UserId**;
2. resolved **OrganizationId** the user is operating in;
3. proof of **membership** linking user to organization.

```text
Authenticated User  +  Organization Membership  →  Tenant Context
```

### 4.3 Organization selection

Support three resolution strategies (in priority order for business routes):

| Strategy | Description | Phase |
|----------|-------------|-------|
| **Explicit header** | Client sends `X-Organization-ID`; server validates membership | Phase 1 |
| **Default organization** | When user belongs to exactly one org, implicit default | Phase 2 |
| **Token claim** | Organization embedded in signed token (`org_id` claim) | Phase 2+ |

Rules:

- if header and token claim both present, they **must agree** or request fails with
  `422` (invalid tenant selection), not silent override;
- if user belongs to zero organizations, business routes return `403`;
- if user belongs to multiple organizations and none is selected, return `422` with
  stable error code (`organization_context_required`).

### 4.4 Request identity propagation

Propagation path (target architecture):

```text
FastAPI dependency: get_security_context()
    ↓
Router builds Command/Query with:
    organization_id: OrganizationId
    actor_user_id: UserId          # new field on commands where audit needed
    ↓
Application handler:
    membership port check (new)
    existing validate_knowledge_object_organization (unchanged)
    ↓
Repository criteria include organization_id (unchanged)
```

**Key constraint:** existing Command/Query types already carry `organization_id`.
Authentication adds **validation** and **actor identity**; it does not remove
organization fields from Application contracts.

### 4.5 Interaction with existing handlers

| Concern | Layer | Change in future implementation |
|---------|-------|----------------------------------|
| Parse JWT / session | API / Bootstrap | New |
| Verify user is org member | Application (via port) | New |
| Verify KO/relation belongs to org | Application (existing validators) | **Unchanged** |
| SQL org filter | Infrastructure repositories | **Unchanged** |
| Cross-org 404 masking | Application | **Unchanged** |

Search, traversal, and mutation handlers continue to receive `OrganizationId` from
tenant context resolution, not from unvalidated headers.

---

## 5. Authentication Architecture

### 5.1 Authentication entry point

Primary entry point: **HTTP Authorization header** on business routes.

Recommended default:

```text
Authorization: Bearer <access_token>
```

Secondary (future): API keys for service accounts, documented separately.

System routes remain unauthenticated. Readiness and health must not require tokens.

### 5.2 Token strategy

Recommended approach for SafetyMAIN MVP implementation (P3-003+):

| Aspect | Decision |
|--------|----------|
| Format | Signed JWT access tokens |
| Signing | Asymmetric keys (RS256 or EdDSA) |
| Validation | Local signature + claims check (no introspection in MVP) |
| Lifetime | Short-lived access token; refresh token in later phase |
| Claims (minimum) | `sub` (user id), `exp`, `iat`, optional `org_id` |
| Storage | Stateless at API layer; no server session store in MVP |

OIDC federation (Azure AD / corporate IdP) is a **future adapter** behind the same
`AuthenticationService` port — not a separate architectural path.

### 5.3 Request authentication flow

```text
Client Request
    │
    ▼
RequestIdMiddleware                    (existing)
    │
    ▼
AuthenticationMiddleware / Dependency
    │  extract Bearer token
    │  validate signature + expiry
    │  map sub → UserId
    ▼
TenantContextDependency
    │  resolve OrganizationId (header / claim / default)
    │  verify membership via MembershipPort
    ▼
Router
    │  build Command / Query
    ▼
Application Handler                    (existing + membership)
    │
    ▼
Infrastructure
```

Failure modes use the **existing error envelope** (`APIErrorResponse`):

| Condition | HTTP | Public code (planned) |
|-----------|------|------------------------|
| Missing / invalid token | 401 | `unauthenticated` |
| Valid user, not org member | 403 | `organization_access_denied` |
| Ambiguous org selection | 422 | `organization_context_required` |
| Object in other org | 404 | `knowledge_object_not_found` (unchanged) |

Internal exception text and token details never appear in responses.

### 5.4 Security dependencies (FastAPI)

Planned dependency chain in `backend/api/dependencies.py` (future tasks):

```text
get_authenticated_user()      → UserId
get_tenant_context()          → TenantContext (UserId + OrganizationId)
get_organization_id()         → OrganizationId  (evolves from header-only)
```

Routers depend on **`get_tenant_context()`** or composed helpers, not on raw headers.

Test strategy mirrors existing patterns:

- FastAPI dependency overrides in `tests/api/conftest.py`;
- contract tests in `tests/api/contracts/` for 401/403/422;
- Application tests use fake `MembershipPort` without HTTP.

### 5.5 Interaction with FastAPI / OpenAPI

Future OpenAPI additions (implementation tasks, not P3-001):

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

Business operations gain `security: [BearerAuth]`. System operations remain open.

`X-Organization-ID` may remain documented as an optional explicit tenant selector during
Phase 1 migration.

---

## 6. Authorization Boundary

Authorization answers: **“Is this authenticated user allowed to perform this
operation in this organization?”**

### 6.1 Layer responsibilities

| Layer | Authentication | Authorization (MVP) | Must not |
|-------|----------------|----------------------|----------|
| **API** | Extract credentials; build SecurityContext | Route-level “auth required” | Business rules; membership logic |
| **Application** | Consume UserId + OrganizationId | Membership check; existing org validators | Parse JWT; SQL |
| **Domain** | — | Pure rules when expressed as domain policy | Know about HTTP, tokens, users table |
| **Infrastructure** | Token crypto adapter; membership store | Persist membership facts | Decide HTTP status codes |
| **Bootstrap** | Wire auth adapters | — | Leak into Domain |
| **Contracts** | `AuthenticationPort`, `MembershipPort` | Interface only | FastAPI types |

### 6.2 MVP authorization scope

Phase 1 (minimum viable authorization):

```text
authenticated
AND member of organization_id
AND existing organization isolation rules
```

Explicitly **not** in MVP:

- object-level ACLs;
- role-based mutation restrictions (e.g. only admin may delete);
- field-level permissions.

### 6.3 Relationship to existing 404 masking

Two distinct authorization decisions:

| Scenario | Response | Layer |
|----------|----------|-------|
| User not member of requested org | `403 organization_access_denied` | Application (membership port) |
| Object exists but belongs to another org | `404 knowledge_object_not_found` | Application (existing validators) |
| Relation exists but belongs to another org | `404 knowledge_object_relation_not_found` | Application (existing validators) |

Do not unify these into generic `403` — the distinction is an intentional security
property documented in P2-005 contract tests.

### 6.4 Clean Architecture preservation

Dependency rules from `ArchitectureTesting.md` remain in force:

```text
Domain        → no API, no FastAPI, no Bootstrap, no Infrastructure
Application   → no FastAPI, no Infrastructure implementations
Contracts     → ports only
API           → no repository implementations, no SQLAlchemy
Bootstrap     → sole composition root for concrete adapters
```

New authentication modules must be covered by architecture tests forbidding:

- JWT/FastAPI imports in Application handlers;
- SQLAlchemy in API dependencies;
- membership checks inside routers (beyond dependency wiring).

---

## 7. User Model (Future Domain Concepts)

Implemented in **P3-002**. See [IdentityDomain.md](IdentityDomain.md) for the
concrete domain model, repository contracts, and application ports.

Membership verification is deferred to future authorization tasks.

Authorization foundation: [AuthorizationFoundation.md](AuthorizationFoundation.md).

Tenant context migration: [TenantContextMigration.md](TenantContextMigration.md).

The following concepts guided P3-002 and remain the architectural baseline:

### 7.1 User

Represents a platform identity.

Conceptual fields:

- `UserId` (value object, immutable)
- display name / email (profile attributes)
- lifecycle status (`active`, `suspended`, `deactivated`)
- external subject reference (optional, for OIDC)

Users are **not** embedded inside Knowledge Object aggregates.

### 7.2 Organization

Today only `OrganizationId` exists as a value object. P3-002 may introduce an
**Organization** entity or aggregate for membership and profile metadata.

Organization remains the tenant boundary regardless of entity introduction timing.

### 7.3 Organization Membership

Links `UserId` to `OrganizationId`.

Conceptual fields:

- membership id
- user id
- organization id
- membership status (`active`, `invited`, `revoked`)
- joined at / revoked at

Membership is the **authorization fact** checked before business handler execution.

### 7.4 Role (high level)

Named collection of permissions within an organization (e.g. `admin`, `member`,
`auditor`).

Roles belong to the **membership** context, not to individual Knowledge Objects.

MVP may collapse to a single implicit `member` role with full org access; the model
must allow evolution without breaking handlers.

### 7.5 Permission (high level)

Atomic capability (e.g. `knowledge_object:read`, `knowledge_object:write`,
`relation:manage`).

Not enforced in MVP. Documented now to prevent ad hoc role checks in routers later.

Permission evaluation belongs in Application services backed by Domain policy — not in
FastAPI dependencies beyond coarse “authenticated + member”.

---

## 8. Migration Strategy

Goal: replace blind trust in `X-Organization-ID` without breaking existing Application
use cases.

### Phase 0 — Baseline (current, P2 complete)

- Header required; any UUID accepted
- No authentication
- Application org isolation enforced

### Phase 1 — Authenticated + validated header (P3-003 target)

- Introduce Bearer token authentication on business routes
- Keep `X-Organization-ID` as explicit tenant selector
- Add membership check: user must belong to header organization
- Application Commands/Queries unchanged; add optional `actor_user_id` where auditing
  requires it
- API tests: extend `test_organization_header.py` → auth + membership cases
- **Backward incompatibility:** unauthenticated clients receive `401` (documented)

### Phase 2 — Token claims and default organization (P3-004+)

- Support `org_id` claim in JWT
- Reconcile header vs claim
- Auto-select when user has single membership
- Deprecation notice for header-only clients

### Phase 3 — Fine-grained authorization (future)

- Roles and permissions on membership
- Object-level policies only where constitution requires

### Compatibility principles

1. **Application handler signatures** change minimally — add fields, do not remove
   `organization_id`.
2. **Repository contracts** unchanged for org scoping.
3. **404 masking** unchanged for cross-org resource access.
4. **Error envelope** extended, not replaced.
5. **In-memory tests** continue using dependency overrides; add fake membership port.

### Rollout safeguards

- Feature flag in Bootstrap settings: `AUTH_ENFORCEMENT=off|shadow|on`
- Shadow mode: log would-be 401/403 without rejecting (non-production only)
- Contract test suite gates OpenAPI and behavior before default-on in production

---

## 9. Architectural Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| AD-AUTH-001 | Organization remains primary tenant boundary | Constitution Article VIII |
| AD-AUTH-002 | JWT bearer tokens for MVP | Stateless, OpenAPI-friendly, testable |
| AD-AUTH-003 | Membership check in Application via port | Preserves Clean Architecture |
| AD-AUTH-004 | Keep 404 masking for cross-org resources | Existing security contract |
| AD-AUTH-005 | Use 403 for membership failures | Distinguishes authz from missing objects |
| AD-AUTH-006 | No auth on system routes | Health/readiness operability |
| AD-AUTH-007 | SecurityContext immutable per request | Predictable handler behavior |
| AD-AUTH-008 | Defer Organization aggregate to P3-002 | ReviewV1 — org as VO today |
| AD-AUTH-009 | Extend error_codes registry, not ad hoc responses | P2-005 contract stability |
| AD-AUTH-010 | OIDC as Infrastructure adapter behind port | Avoid API layer fork |

---

## 10. Future Implementation Roadmap

| Task | Deliverable |
|------|-------------|
| **P3-002** | User and Organization Domain — entities, VOs, membership model |
| **P3-003** | Authentication API — JWT infrastructure, login/refresh endpoints |
| **P3-004** | Authorization Foundation — membership verification and policies |
| **P3-005** | Tenant Context Migration — authenticated business API integration |
| **P3-006** | Role-Based Authorization — roles and permission evaluation |
| **P3-007** | OIDC / enterprise IdP adapter (optional track) |

Each task must include architecture test updates and contract tests before behavior
is enabled by default.

---

## 11. Verification (P3-001)

This task delivers documentation only.

| Criterion | Status |
|-----------|--------|
| Authentication architecture documented | This document |
| Identity model defined | §3 |
| Tenant context strategy defined | §4 |
| Authorization boundaries documented | §6 |
| Clean Architecture preserved | §6.4 |
| Migration strategy documented | §8 |
| No API behavior changes | No code modified |
| No persistence changes | No code modified |
| No new endpoints | No code modified |

Post-implementation verification (future tasks):

```bash
python3 -m pytest
python3 -m ruff check .
```

Architecture tests must be extended for auth module boundaries before P3-003 merges.

---

## 12. Summary

SafetyMAIN adopts a **fail-closed, organization-scoped** authentication model:

- users authenticate at the HTTP boundary with Bearer JWT;
- tenant context replaces blind header trust through membership validation;
- Application handlers retain existing organization isolation;
- authorization grows from membership outward to roles and permissions;
- migration is phased to protect Application use cases and HTTP contracts.

The project is ready to begin **P3-002 — User and Organization Domain**.
