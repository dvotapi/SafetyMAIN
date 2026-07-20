# Identity and Organization Domain

Status: Active  
Date: 2026-07-21  
Task: TASK-P3-002

Related documents:

- [AuthenticationArchitecture.md](AuthenticationArchitecture.md) — authentication blueprint
- [ArchitectureConstitution.md](ArchitectureConstitution.md) — Article VIII

---

## 1. Purpose

This document describes the domain foundation for platform identity: users,
organizations, memberships, roles, and permissions.

TASK-P3-002 introduces **domain models and contracts only**. No HTTP endpoints,
authentication implementation, or persistence adapters are included.

---

## 2. Domain Relationships

```text
User ──< Membership >── Organization
              │
              └── Role ──> Permission (conceptual mapping)
```

| Concept | Role in architecture |
|---------|----------------------|
| **User** | Platform identity independent of authentication transport |
| **Organization** | Tenant boundary and ownership scope |
| **Membership** | Authorization fact linking user to organization |
| **Role** | Named capability set assigned through membership |
| **Permission** | Atomic capability; mapped to roles, not evaluated yet |

Organization remains the primary tenant boundary. Knowledge Objects continue to
reference `OrganizationId` directly and are not owned by User aggregates.

---

## 3. Domain Model

### 3.1 Value objects

| Type | Module | Notes |
|------|--------|-------|
| `UserId` | `domain/value_objects/user_id.py` | Immutable UUID wrapper |
| `OrganizationId` | `domain/value_objects/organization_id.py` | Existing tenant identifier |
| `MembershipId` | `domain/value_objects/membership_id.py` | Immutable UUID wrapper |
| `Role` | `domain/value_objects/role.py` | Normalized role name; system factories |
| `Permission` | `domain/value_objects/permission.py` | Normalized permission code |

System roles: `admin`, `member`, `auditor`.

System permissions include `knowledge_object:read`, `knowledge_object:write`,
`relation:manage`, `membership:manage`, and `organization:admin`.

Role-to-permission mapping lives in
`domain/value_objects/role_permissions.py`. Permission evaluation is deferred to
future authorization tasks.

### 3.2 Entities

| Entity | Module | Key fields |
|--------|--------|------------|
| `User` | `domain/entities/user.py` | `UserId`, email, display name, lifecycle status, optional external subject |
| `Organization` | `domain/entities/organization.py` | `OrganizationId`, name |
| `Membership` | `domain/entities/membership.py` | user/org ids, status, role, joined/revoked timestamps |

User lifecycle: `ACTIVE`, `SUSPENDED`, `DEACTIVATED`.

Membership lifecycle: `ACTIVE`, `INVITED`, `REVOKED`.

Active membership grants organization access through
`Membership.grants_organization_access()`.

### 3.3 Domain services

`MembershipService` (`domain/services/membership_service.py`) enforces membership
lifecycle transitions:

- activate invited membership;
- revoke active or invited membership;
- reject reactivation of revoked membership;
- raise `InactiveMembership` when access is required but not granted.

### 3.4 Domain exceptions

| Base | Examples |
|------|----------|
| `UserError` | `UserNotFound` |
| `OrganizationError` | `OrganizationNotFound` |
| `MembershipError` | `MembershipNotFound`, `InactiveMembership`, transition guards |

All inherit from `SafetyMainDomainError`.

---

## 4. Repository Contracts

Repository Protocols live in `backend/core/domain/repositories/` following the
Knowledge Object pattern.

| Contract | Responsibilities |
|----------|------------------|
| `UserRepositoryContract` | add/get/get_by_email/save |
| `OrganizationRepositoryContract` | add/get/save |
| `MembershipRepositoryContract` | add/get/get_by_user_and_organization/list/save |

Repositories persist domain facts only. They do not perform HTTP-facing
authorization decisions.

Concrete adapters (in-memory, SQLAlchemy) are implemented in later tasks.

---

## 5. Application Ports

Application ports live in `backend/core/contracts/` and remain transport-free.

| Port | Module | Purpose |
|------|--------|---------|
| `UserLookupPort` | `contracts/user_lookup.py` | Resolve users by id or external subject |
| `MembershipLookupPort` | `contracts/membership_lookup.py` | Resolve memberships for tenant selection |
| `OrganizationMembershipVerificationPort` | `contracts/organization_membership_verification.py` | Verify active membership before business handlers |

No Application handler consumes these ports yet. Wiring begins in P3-003+.

---

## 6. Clean Architecture Placement

```text
Domain entities / VOs / repository Protocols
        ↑
Contracts ports (UserLookup, MembershipLookup, Verification)
        ↑
Application handlers (future)
        ↑
Infrastructure adapters (future)
        ↑
API / Bootstrap (future)
```

Domain modules must not import Application, Infrastructure, API, or Bootstrap.

---

## 7. Next Steps

| Task | Deliverable |
|------|-------------|
| **P3-003** | Authentication API and token validation wiring |
| **P3-004** | Application membership services consuming ports |
| **P3-006** | Persistence tables and repository adapters |

See [AuthenticationArchitecture.md](AuthenticationArchitecture.md) for the full
authentication roadmap.
