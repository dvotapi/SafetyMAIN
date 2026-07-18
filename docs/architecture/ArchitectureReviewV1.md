# Architecture Review V1

Version: 1.0

Status: Reviewed

Date: 2026-07-19

---

# 1. Current Architecture

SafetyMAIN Core is organized around Clean Architecture boundaries.

- Domain contains Knowledge Object entities, relation entities, value objects, domain events, domain exceptions, repository contracts and domain services.
- Application contains commands, queries and handlers for lifecycle, relation traversal and search use cases.
- Contracts define Unit of Work and infrastructure-facing ports.
- In-memory infrastructure provides deterministic adapters for local tests and early use cases.
- SQLAlchemy infrastructure provides PostgreSQL mappings, repositories and Unit of Work implementations.
- Alembic manages schema creation for Knowledge Objects, version history and relations.
- Architecture tests enforce forbidden imports between domain, application, contracts and infrastructure layers.

# 2. Dependency Direction

The implemented dependency direction follows:

```text
Infrastructure -> Application/Contracts -> Domain
```

Domain does not import SQLAlchemy, Alembic, concrete adapters or application handlers.

Application depends on domain and contracts, not concrete infrastructure.

Contracts remain independent from concrete infrastructure implementations.

Infrastructure imports domain contracts and entities where mapping requires it.

# 3. Domain Model Review

Knowledge Objects have an explicit lifecycle: `DRAFT`, `ACTIVE`, `ARCHIVED`, `DELETED`.

Version history is immutable and stores previous versions only.

Relations are directed, organization-scoped and use extensible relation types rather than enums.

Traversal is one-hop only and supports outgoing, incoming and both-direction reads.

Structured search is organization-scoped, deterministic and supports exact top-level metadata matching.

Organization boundaries are consistently represented by `OrganizationId`. Cross-organization relation prevention is enforced by the domain service; the database schema supports efficient organization filtering but does not fully enforce cross-organization consistency without introducing an Organization aggregate.

# 4. Contract Review

`KnowledgeObjectRepositoryContract` exposes infrastructure-independent operations: `add`, `get`, `update`, `history`, `search`.

`KnowledgeObjectRelationRepositoryContract` is separate and exposes relation-specific operations: `add`, `get`, `remove`, `exists`, `outgoing`, `incoming`.

`UnitOfWorkContract` exposes both repositories and transaction operations through a synchronous context manager.

No contract currently exposes SQLAlchemy, PostgreSQL, HTTP or framework-specific types.

# 5. Transaction Review

Repositories do not commit, rollback, close sessions or create sessions.

Unit of Work owns commit and rollback.

SQLAlchemy Knowledge Object updates append the previous version to history and update the current row in the same transaction.

SQLAlchemy Unit of Work shares one Session across Knowledge Object and Relation repositories.

In-memory Unit of Work was aligned with SQLAlchemy semantics: exit without commit rolls back.

# 6. Persistence Review

SQLAlchemy mappings are kept in the infrastructure layer.

Mapping helpers explicitly convert between domain entities and persistence models.

Alembic migrations define:

- `knowledge_objects`
- `knowledge_object_versions`
- `knowledge_object_relations`

The schema includes unique constraints for object history versions and directed relations, a self-reference check for relations, foreign keys for relation endpoints and indexes for current access patterns.

JSONB search is implemented in PostgreSQL through SQLAlchemy expressions. Metadata equality remains type-sensitive in the observable contract.

Expected repository errors are translated to typed domain exceptions. Transaction rollback after flush-time infrastructure failures remains the Unit of Work responsibility.

# 7. Testing Review

Point-in-time local verification after contract suites:

- `python3 -m pytest` reported 136 passed and 60 skipped before PostgreSQL DB execution.
- `python3 -m ruff check .` passed.
- Architecture tests run as part of normal pytest.
- Reusable contract suites now cover Knowledge Object repository, Relation repository and Unit of Work behavior.
- SQLAlchemy contract tests are marked `db` and skipped unless PostgreSQL DB tests are explicitly enabled.

Real PostgreSQL workflow was attempted, but Docker Compose was unavailable and the Docker daemon was not running in this environment. DB validation commands are documented and must be run in an environment with Docker/PostgreSQL available.

# 8. Technical Debt

## Blocking Before API

No blocking architectural issue was found in the Core layer itself.

Problem: real PostgreSQL contract tests were not executed in this environment.

Consequence: PostgreSQL adapter behavior is covered structurally and by skipped integration tests, but not verified against a live database in this run.

Recommendation: run the documented DB workflow before starting API integration work.

## Should Address Soon

Problem: SQLAlchemy DB fixtures currently reset schema per test through Alembic downgrade/upgrade.

Consequence: DB tests are deterministic but may become slow as migrations grow.

Recommendation: introduce a faster isolated DB cleanup strategy after repository behavior stabilizes.

Problem: SQLAlchemy flush-time integrity errors require external rollback.

Consequence: callers must not reuse a failed session before the Unit of Work rolls back.

Recommendation: cover this clearly in future SQLAlchemy Unit of Work integration tests and API error paths.

## Acceptable For MVP

Problem: cross-organization relation integrity is enforced by domain service rather than full database-level composite constraints.

Consequence: direct database writes could violate organization consistency.

Recommendation: keep domain enforcement for MVP; revisit when Organization aggregate and production repository adapters mature.

## Future Enhancement

Problem: architecture tests enforce dependency direction but not all possible third-party infrastructure libraries.

Consequence: a new unsupported library could slip through if not listed.

Recommendation: expand forbidden prefixes as infrastructure choices grow.

# 9. Decision

READY WITH CONDITIONS

Reasons:

- Core domain, application, contracts and infrastructure boundaries are clean.
- In-memory and SQLAlchemy adapters now share reusable observable contract tests.
- Unit of Work semantics are aligned.
- Architecture tests and Ruff pass locally.
- The only condition is successful live PostgreSQL validation in an environment with Docker/PostgreSQL available.
