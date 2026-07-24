# Persistent Identity and Membership Stores

Status: Active  
Date: 2026-07-24  
Task: TASK-P7-001

Related documents:

- [IdentityPersistence.md](IdentityPersistence.md)
- [IdentityDomain.md](IdentityDomain.md)
- [AuthenticationArchitecture.md](AuthenticationArchitecture.md)
- [AuthorizationFoundation.md](AuthorizationFoundation.md)
- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)
- [TenantContextMigration.md](TenantContextMigration.md)
- [SecurityArchitectureReview.md](SecurityArchitectureReview.md)
- [SecurityOperationsArchitectureReview.md](SecurityOperationsArchitectureReview.md)
- [RefreshTokenSessions.md](RefreshTokenSessions.md)

---

## 1. Source-of-Truth Model

PostgreSQL is the production source of truth for:

| Concern | Authoritative store |
|---------|---------------------|
| User identity | `users` |
| User active status | `users.is_active` |
| Organization identity | `organizations` |
| Membership existence | `memberships` |
| Membership active status | `memberships.is_active` |
| Membership role | `memberships.role` |
| Tenant eligibility | active membership row |
| Authorization role resolution | active membership role via ports |
| Refresh-token session validity | `refresh_token_sessions` (P7-002) |

Authentication, tenant resolution, and RBAC must not depend on process-local mutable
collections in production.

In-memory repositories and stores remain available only for:

- unit tests;
- isolated application tests;
- explicit non-production fixtures when `DATABASE_URL` is unset.

There is no dual-write between PostgreSQL and in-memory stores.

---

## 2. Inventory

### Repository contracts

| Contract | Path |
|----------|------|
| `UserRepositoryContract` | `backend/core/domain/repositories/user_repository.py` |
| `OrganizationRepositoryContract` | `backend/core/domain/repositories/organization_repository.py` |
| `MembershipRepositoryContract` | `backend/core/domain/repositories/membership_repository.py` |
| `InvitationRepositoryContract` | `backend/core/domain/repositories/invitation_repository.py` |

### Production implementations

| Implementation | Path |
|----------------|------|
| `SQLAlchemyUserRepository` | `.../sqlalchemy/repositories/user_repository.py` |
| `SQLAlchemyOrganizationRepository` | `.../sqlalchemy/repositories/organization_repository.py` |
| `SQLAlchemyMembershipRepository` | `.../sqlalchemy/repositories/membership_repository.py` |
| `SQLAlchemyInvitationRepository` | `.../sqlalchemy/repositories/invitation_repository.py` |
| `SQLAlchemyUnitOfWork` | `.../sqlalchemy/unit_of_work.py` |

### Auth/tenant ports (read adapters)

| Adapter | Ports | Path |
|---------|-------|------|
| `SQLAlchemyIdentityAdapter` | `UserLookupPort`, `UserCredentialsPort` | `backend/core/infrastructure/auth/sqlalchemy_identity_adapter.py` |
| `SQLAlchemyMembershipAdapter` | `MembershipLookupPort`, `MembershipVerificationPort` | `backend/core/infrastructure/auth/sqlalchemy_membership_adapter.py` |

### Test implementations

| Implementation | Path |
|----------------|------|
| `InMemoryUserRepository` | `.../in_memory/user_repository.py` |
| `InMemoryOrganizationRepository` | `.../in_memory/organization_repository.py` |
| `InMemoryMembershipRepository` | `.../in_memory/membership_repository.py` |
| `InMemoryUnitOfWork` | `.../in_memory/unit_of_work.py` |
| `InMemoryIdentityStore` | `backend/core/infrastructure/auth/in_memory_identity_store.py` |
| `InMemoryMembershipStore` | `backend/core/infrastructure/auth/in_memory_membership_store.py` |

### Models and mappers

| Model | Mapper |
|-------|--------|
| `UserModel` | `user_mapper.py` |
| `OrganizationModel` | `organization_mapper.py` |
| `MembershipModel` | `membership_mapper.py` |
| `InvitationModel` | `invitation_mapper.py` |

Domain entities (`User`, `Organization`, `Membership`, `Invitation`) and value objects
remain independent of SQLAlchemy sessions, ORM relationships, and FastAPI.

---

## 3. Dependency Injection

`backend/bootstrap/container.py` → `create_container()`:

```text
DATABASE_URL set
  → SQLAlchemyIdentityAdapter
  → SQLAlchemyMembershipAdapter
  → SQLAlchemyUnitOfWork via uow_factory

DATABASE_URL unset (non-production)
  → InMemoryIdentityStore / InMemoryMembershipStore
  → uow_factory raises RuntimeError("Database is not configured.")

APP_ENV=production
  → DATABASE_URL required (security validation)
  → in-memory identity/membership injection rejected
  → no silent empty in-memory fallback
```

Handlers depend on contracts / ports. API routes do not instantiate repositories.

---

## 4. Unit of Work

One SQLAlchemy `Session` per Unit of Work. Identity, membership, invitation, and audit
repositories share that session. Repositories flush for constraint detection but never
`commit()`. Commit/rollback belong to `SQLAlchemyUnitOfWork`.

Invitation acceptance provisions membership and updates invitation status in one
business transaction via the shared UoW.

---

## 5. User Persistence

Persisted fields: id, email, password_hash, display_name, is_active, external_subject,
created_at, updated_at.

Email normalization: `strip().lower()` on the `User` entity and again on repository
lookup. Uniqueness: `uq_users_email`.

Contract methods used by handlers: `add`, `get`, `get_by_email`, `save`, `list_users`.

Password hashes are opaque. Plaintext passwords never enter repositories. Credential
verification remains on `PasswordHasherContract` outside persistence models.

Inactive users remain retrievable and are rejected by authentication policy
(`User.can_authenticate()`).

---

## 6. Organization Persistence

Persisted fields: id, name, is_active, created_at, updated_at.

Contract methods: `add`, `get`, `save`, `get_by_normalized_name`, `list_organizations`.

Organization listing for a user is membership-driven through membership repositories /
ports, not through a user-owned organization collection on the organization repository.

---

## 7. Membership Persistence

### Uniqueness rule

```text
one membership record per (user_id, organization_id)
```

Deactivation updates the existing row (`is_active=false`). Historical multi-row
membership timelines are not modeled.

Enforced at:

- application handlers (`DuplicateMembership` pre-check);
- repository uniqueness parity (in-memory);
- PostgreSQL `uq_memberships_user_organization`;
- IntegrityError mapping to `DuplicateMembership`.

### Role persistence

Canonical values: `admin`, `member`, `auditor` (`SystemRole`).

- Writes validated by `validate_membership_role` in application handlers.
- Database CHECK `ck_memberships_role_system` (Alembic `0008_membership_role_check`).
- Unknown legacy role strings grant **no** permissions via `RolePermissionResolver`
  (empty set). Role parsing never defaults to an elevated role.

### Active membership

Inactive memberships do not grant tenant access (`grants_organization_access()`) and
do not grant permissions.

---

## 8. Authentication Integration

```text
AuthenticateUserHandler
  → UserLookupPort.get_user_by_email (SQLAlchemyIdentityAdapter)
  → UserCredentialsPort.get_password_hash
  → PasswordHasherContract.verify_password
  → TokenServiceContract.issue_tokens
  → AuthenticationSecurityEventRecorder
```

Production login reads PostgreSQL. JWT claims do not replace membership validation for
authorization. Password hashes are not cached in global mutable state.

---

## 9. Tenant Resolution Integration

`TenantContextResolver` precedence is unchanged:

1. token organization
2. header fallback
3. default organization where configured
4. sole active membership fallback

Conflicts raise `OrganizationContextMismatchError` (HTTP 422). Compatibility vs enforced
behavior continues to follow `AUTH_ENFORCEMENT`.

Membership decisions use `MembershipLookupPort` → PostgreSQL in production.

---

## 10. Authorization Integration

Role for RBAC comes from the current persistent membership loaded through
`MembershipLookupPort` / `MembershipVerificationPort` into `SecurityContext` /
`AuthorizationService`.

Authoritative sources:

| Decision | Source |
|----------|--------|
| Authenticated user id | JWT subject (validated) + user lookup |
| Active membership / current role | Persistent membership row |
| Effective permissions | `RolePermissionResolver` over membership role |

Token role claims are not used as an override of persistent membership state.

Role changes and membership deactivation affect subsequent requests immediately after
commit because adapters open short-lived read sessions.

---

## 11. Constraint Failure Mapping

`backend/core/infrastructure/persistence/sqlalchemy/identity_constraint_errors.py`
maps:

| Constraint | Domain exception |
|------------|------------------|
| `uq_users_email` | `DuplicateUserEmail` |
| `uq_memberships_user_organization` | `DuplicateMembership` |
| `ck_memberships_role_system` | `InvalidMembershipRole` |

SQLAlchemy `IntegrityError` must not reach API responses for these cases. Public status
codes remain 409 / 422 per existing taxonomy.

---

## 12. Concurrency

PostgreSQL unique constraints are the final arbiter for concurrent duplicate email or
membership creation. Competing writers receive mapped domain exceptions. Invitation
double-accept races that attempt a second membership insert are blocked by membership
uniqueness; invitation status transitions remain in the same UoW as membership
provisioning.

Known difference vs in-memory: in-memory repositories are single-process and do not
simulate PostgreSQL isolation; contract behavior for uniqueness and missing records is
aligned, concurrency is not.

---

## 13. Migrations

| Revision | Purpose |
|----------|---------|
| `0002_identity_persistence` | users / organizations / memberships + FKs + uniqueness |
| `0003_organization_active_state` | organization active + name uniqueness |
| `0004_invitations` | invitations |
| `0008_membership_role_check` | membership role CHECK |

`0008` fails with a diagnostic if legacy rows contain unsupported role values. It does
not delete or silently rewrite production data.

---

## 14. Failure Handling and Guardrails

- Missing `DATABASE_URL` in production → `SecurityConfigurationError` at startup.
- Production in-memory store injection → rejected.
- Architecture tests: `tests/architecture/test_p7_persistent_identity_guardrails.py`.
- Contract suites: in-memory + SQLAlchemy (`tests/contracts/test_identity_repository_contracts.py`,
  `tests/contracts/test_sqlalchemy_identity_contracts.py`).
- Concurrency / restart: `tests/infrastructure/test_identity_concurrency.py`,
  `tests/infrastructure/test_identity_restart_persistence.py`.

---

## 15. Known Limitations

1. Administrative `CreateUser` persists users with an empty password hash until a
   separate credential-provisioning path sets one (existing P5 behavior).
2. Membership role/active updates have last-writer-wins semantics under concurrency
   (no optimistic version column).
3. Auth/tenant port adapters use short-lived sessions separate from the request UoW
   used by administrative mutations; committed state is visible on the next read.
4. In-memory stores remain for non-production unset-database workflows and tests only.
