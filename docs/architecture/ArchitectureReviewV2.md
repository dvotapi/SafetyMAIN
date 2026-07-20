# Architecture Review v2

Status: Active  
Date: 2026-07-20  
Task: TASK-P2-005

---

## 1. Current System Boundary

SafetyMAIN follows an entity-centric layered architecture:

| Layer | Responsibility |
|-------|----------------|
| **Domain** | Entities, value objects, domain services, domain exceptions |
| **Application** | Commands, queries, handlers, organization validation |
| **Contracts** | Repository and Unit of Work interfaces |
| **Infrastructure** | In-memory and SQLAlchemy persistence adapters |
| **API** | FastAPI inbound adapter (routers, schemas, mappers, params) |
| **Bootstrap** | Settings, composition root, dependency wiring |

The HTTP API milestone exposes system, Knowledge Object, Relation, traversal, and search endpoints as thin adapters over Application handlers.

---

## 2. HTTP Dependency Direction

Confirmed dependency flow:

```text
API → Application → Contracts → Domain
Bootstrap → API + Infrastructure
Infrastructure → Contracts / Domain
```

Intentional exceptions:

- **Bootstrap** imports concrete SQLAlchemy and in-memory adapters for composition.
- **API schemas** use Pydantic for transport models (not Domain entities).
- **Domain value objects** use Pydantic internally for validation/normalization.

No violations were found where Domain or Application import FastAPI, API schemas, or Bootstrap.

---

## 3. API Thinness Review

Routers:

- construct Application commands/queries;
- invoke handlers through FastAPI dependencies;
- map Domain results through dedicated mappers;
- do not implement business rules;
- do not import repository implementations or ORM models;
- do not call `commit()` or `rollback()`.

Fixes applied in TASK-P2-005:

- stable OpenAPI `operationId` values on all 16 business/system routes;
- centralized OpenAPI response helpers (`backend/api/openapi.py`);
- normalized validation error shape;
- explicit architecture guard against router transaction calls.

No remaining router violations were identified.

---

## 4. Organization Isolation Review

Organization context is enforced through:

- mandatory `X-Organization-ID` on all business routes;
- Application-layer organization validation on commands and queries;
- cross-organization access masked as `404 Not Found` for Knowledge Objects and Relations;
- search scoped exclusively to the requested organization.

System routes (`/health`, `/ready`) do not require organization context.

Contract tests verify missing/malformed headers return `422`, and cross-organization access returns `404`.

---

## 5. Transaction Review

Confirmed behavior:

- request-scoped UoW via FastAPI dependency;
- dependency enters/exits UoW without committing;
- command handlers own commit decisions;
- query handlers do not commit;
- failed commands roll back through UoW context exit when not committed.

Representative verification covers create/update/delete/search and UoW dependency lifecycle tests.

---

## 6. API Contract Review

Normalized in TASK-P2-005:

| Area | Decision |
|------|----------|
| Error envelope | `{error: {code, message, details}}` on all handled failures |
| `details` | Always present; includes `request_id` at minimum |
| Validation | `request_validation_error` + `violations[]` with `location`, `message`, `type` |
| Public codes | Central registry in `backend/api/error_codes.py` |
| Success statuses | Documented per route (201 create, 204 delete, 200 otherwise) |
| No-content DELETE | Empty body, documented in OpenAPI without content schema |
| Create Location | Relative URI documented in OpenAPI |
| Request ID | `X-Request-ID` on every response |
| Timestamps | ISO 8601 UTC in JSON responses |
| Metadata | JSON types preserved across create/get/update/history/search |
| OpenAPI | Stable operation IDs, organization header on business routes |

---

## 7. Testing Review

Point-in-time verification (2026-07-20):

| Category | Result |
|----------|--------|
| Total tests | **307 passed**, **60 skipped** |
| API tests | `tests/api/` including contract suites |
| Contract tests | `tests/api/contracts/` |
| Architecture tests | `tests/architecture/` (import and method-call guards) |
| OpenAPI tests | operation IDs, headers, 204 responses |
| DB contract tests | skipped without `SAFETYMAIN_RUN_DB_TESTS=1` |

Contract coverage added:

- error envelope consistency;
- request ID behavior;
- organization header requirements;
- no-content DELETE responses;
- Location headers on create;
- OpenAPI contract assertions;
- lifecycle, relation, search, and metadata round-trip scenarios.

---

## 8. Live PostgreSQL Validation

**Status: complete (2026-07-20).**

Executed validation workflow:

```text
Alembic upgrade head
DB tests (pytest -m db)
Alembic downgrade base
Alembic upgrade head
DB tests (repeat)
Full suite with SAFETYMAIN_RUN_DB_TESTS=1
```

See [PostgreSQLValidation.md](../persistence/PostgreSQLValidation.md) for commands, results, and persistence fixes applied during validation.

Verified through live PostgreSQL:

- migration lifecycle (upgrade/downgrade/re-upgrade);
- SQLAlchemy repository contract suites;
- Unit of Work transaction behavior;
- readiness endpoint against real database;
- HTTP smoke tests with production wiring;
- JSON type-sensitive search semantics.

---

## 9. Technical Debt

### Blocking before authentication

| Issue | Impact | Recommendation |
|-------|--------|----------------|
| Temporary organization header only | No caller identity or membership | Implement authentication foundation next |

### Should address soon

| Issue | Impact | Recommendation |
|-------|--------|----------------|
| Draft objects excluded from default search | Clients must understand lifecycle/search interaction | Document clearly (done in search API doc) |
| `cross_organization_knowledge_object_relation` code unused at HTTP layer | Registry/code divergence | Keep for Application completeness; HTTP uses 404 masking |

### Acceptable for MVP

| Issue | Impact | Recommendation |
|-------|--------|----------------|
| No rate limiting / idempotency | Operational protection deferred | Add with authentication phase |
| Starlette TestClient deprecation warning | Test noise only | Migrate to httpx2 when convenient |

### Future enhancement

| Issue | Impact | Recommendation |
|-------|--------|----------------|
| Generated OpenAPI client publication | External SDK automation | After authentication stabilizes |
| OpenTelemetry / structured access logs | Observability | Post-MVP operations work |

---

## 10. Decision

## READY FOR AUTHENTICATION FOUNDATION

The first HTTP API milestone and persistence layer are validated against live PostgreSQL.

Reasons:

- Alembic migration lifecycle succeeds on PostgreSQL 17;
- all DB-marked tests pass (64 tests);
- full suite passes with `SAFETYMAIN_RUN_DB_TESTS=1` (371 tests);
- readiness and HTTP smoke tests succeed against real database wiring;
- API contract is stable and documented;
- organization isolation and transaction ownership are verified.

Proceed to **P3-001 — Identity and Authentication Architecture** (design), then
**P3-002 — User and Organization Domain** (implementation).

See [AuthenticationArchitecture.md](AuthenticationArchitecture.md).
