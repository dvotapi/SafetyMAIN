# TASK-P1-002

## Title

Implement SQLAlchemy Knowledge Object Repository

## Goal

Implement a SQLAlchemy-backed adapter for the existing `KnowledgeObjectRepositoryContract`.

The adapter shall persist Knowledge Objects and their immutable version history using the PostgreSQL schema introduced in `TASK-P1-001`.

The Domain and Application layers must remain unchanged.

## Acceptance Criteria

- SQLAlchemy Knowledge Object repository implements the existing contract.
- Domain entities are mapped explicitly to and from persistence models.
- Add, get, update, history, and search are implemented.
- Repository never commits or creates its own session.
- Updates append the previous version to immutable history.
- Version conflicts raise typed domain exceptions.
- Search executes in PostgreSQL rather than Python memory.
- Organization isolation is always enforced in search.
- JSON metadata comparison preserves current type-sensitive semantics.
- Repository returns Domain entities only.
- Raw SQLAlchemy and PostgreSQL exceptions do not leak through expected domain error paths.
- In-memory behavior remains unchanged.
- Existing tests pass.
- PostgreSQL repository tests pass when the DB test environment is available.
- Ruff passes.
- Import validation passes.
- Architecture tests pass.
- Alembic upgrade and downgrade work.
