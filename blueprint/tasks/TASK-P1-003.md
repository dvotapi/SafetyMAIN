# TASK-P1-003

## Title

Implement SQLAlchemy Knowledge Object Relation Repository

## Goal

Implement a SQLAlchemy-backed adapter for the existing `KnowledgeObjectRelationRepositoryContract`.

The adapter shall persist directed Knowledge Object relations using the PostgreSQL schema introduced in `TASK-P1-001`.

The Domain and Application layers must remain unchanged.

## Acceptance Criteria

- SQLAlchemy relation repository implements the existing contract.
- Domain relations are explicitly mapped to and from persistence models.
- Add, get, remove, exists, outgoing and incoming are implemented.
- Repository uses an externally supplied Session.
- Repository never commits, rolls back or creates its own session.
- Duplicate directed relations raise `DuplicateKnowledgeObjectRelation`.
- Reverse relations remain valid.
- Self-reference violations raise `SelfReferencingKnowledgeObjectRelation`.
- Missing relations raise `KnowledgeObjectRelationNotFound`.
- Traversal is organization-scoped.
- Traversal filtering and ordering execute in PostgreSQL.
- Traversal results are immutable and deterministic.
- Raw expected SQLAlchemy and PostgreSQL exceptions do not leak.
- Existing in-memory behavior remains unchanged.
- Existing tests pass.
- PostgreSQL relation tests pass when the DB environment is available.
- Ruff passes.
- Import validation passes.
- Architecture tests pass.
- Alembic upgrade and downgrade work.
