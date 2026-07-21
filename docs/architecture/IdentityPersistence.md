# Identity Persistence

Status: Active  
Date: 2026-07-21  
Task: TASK-P4-001

Related documents:

- [IdentityDomain.md](IdentityDomain.md)
- [AuthenticationArchitecture.md](AuthenticationArchitecture.md)
- [AuthorizationFoundation.md](AuthorizationFoundation.md)
- [SecurityArchitectureReview.md](SecurityArchitectureReview.md)
- [UserManagement.md](UserManagement.md)
- [PostgreSQLPersistence.md](../infrastructure/PostgreSQLPersistence.md)

---

## 1. Purpose

This document describes SQLAlchemy persistence for users, organizations, and
memberships introduced in P4-001. The temporary in-memory identity adapters remain
available when `DATABASE_URL` is not configured.

Authentication handlers, authorization services, and public API behavior remain
unchanged.

---

## 2. Persistence Model

| Table | Domain entity | Notes |
|-------|---------------|-------|
| `users` | `User` | Includes `password_hash`, `display_name`, and `updated_at` |
| `organizations` | `Organization` | Tenant organization record |
| `memberships` | `Membership` | Role and active state for user/org pairing |

Domain mapping:

- `users.is_active` ↔ `UserStatus.ACTIVE`
- `memberships.is_active` ↔ `MembershipStatus.ACTIVE`
- `memberships.role` ↔ domain `Role`

Alembic revision: `0002_identity_persistence`.

---

## 3. Repository Mapping

| Domain contract | SQLAlchemy implementation |
|-----------------|---------------------------|
| `UserRepositoryContract` | `SQLAlchemyUserRepository` |
| `OrganizationRepositoryContract` | `SQLAlchemyOrganizationRepository` |
| `MembershipRepositoryContract` | `SQLAlchemyMembershipRepository` |

Repositories live under
`backend/core/infrastructure/persistence/sqlalchemy/repositories/` and follow the
same session-per-UnitOfWork pattern as Knowledge Object repositories.

---

## 4. Application Port Adapters

Authentication and authorization continue to depend on Application ports:

| Port | SQLAlchemy adapter |
|------|--------------------|
| `UserLookupPort` | `SQLAlchemyIdentityAdapter` |
| `UserCredentialsPort` | `SQLAlchemyIdentityAdapter` |
| `MembershipLookupPort` | `SQLAlchemyMembershipAdapter` |
| `MembershipVerificationPort` | `SQLAlchemyMembershipAdapter` |

Port adapters open short-lived read sessions. They do not replace UnitOfWork
transaction ownership for business use cases.

---

## 5. Transaction Flow

```text
Business handlers
    ↓
SQLAlchemyUnitOfWork
    ↓
Knowledge Object / Relation / Identity repositories (shared Session)
    ↓
commit() or rollback()
```

Authentication lookups:

```text
AuthenticateUserHandler
    ↓
UserLookupPort / UserCredentialsPort
    ↓
SQLAlchemyIdentityAdapter (read session)
    ↓
users table
```

Authorization lookups:

```text
AuthorizationService / PermissionEvaluator
    ↓
MembershipLookupPort / MembershipVerificationPort
    ↓
SQLAlchemyMembershipAdapter (read session)
    ↓
memberships table
```

---

## 6. Dependency Injection

`create_container()` selects adapters based on configuration:

- `DATABASE_URL` configured → SQLAlchemy identity/membership adapters
- no database → `InMemoryIdentityStore` / `InMemoryMembershipStore`

Tests may override stores explicitly through `create_container(...)` parameters.

---

## 7. Development Seed Data

Module: `backend/bootstrap/seed_identity.py`

Seeds:

- one development organization
- admin, member, and auditor users
- active memberships for each role

Default password: `dev-password`

Seeding is manual and must not run automatically in production.

Example:

```bash
DATABASE_URL=postgresql+psycopg://... python -c "
from backend.bootstrap.container import create_container
from backend.bootstrap.settings import load_settings
from backend.bootstrap.seed_identity import seed_development_identity

settings = load_settings()
container = create_container(settings)
assert container.session_factory is not None
seed_development_identity(container.session_factory, password_hasher=container.password_hasher)
"
```

---

## 8. Migration and Validation

Apply migrations:

```bash
alembic upgrade head
```

Validation coverage:

- metadata tests for identity tables
- Alembic upgrade/downgrade smoke tests
- repository contract suites (in-memory and PostgreSQL)

Production deployments must also satisfy startup security validation documented in
[ProductionSecurityConfiguration.md](ProductionSecurityConfiguration.md), including
a configured `DATABASE_URL` when `APP_ENV=production`.

---

## 9. Administrative User API (P5-001)

User records are global identities. The administrative REST API at
`/api/v1/admin/users` reuses `UserRepositoryContract` through Application handlers
and UnitOfWork — no duplicate persistence models or direct SQLAlchemy access from
routers.

Repository capabilities used by administration:

- `get_by_id`, `get_by_email`, `add`, `update` — create, read, update, lifecycle
- `list_users` — offset pagination with optional filters on email, display name, and
  active state

API responses expose public UUIDs and stable DTO fields only. Password hashes and
SQLAlchemy models never cross the HTTP boundary. See
[UserManagement.md](UserManagement.md) and [AdminUserAPI.md](../api/AdminUserAPI.md).
