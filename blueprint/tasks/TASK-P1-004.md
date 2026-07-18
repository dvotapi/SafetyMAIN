# TASK-P1-004

## Title

Implement SQLAlchemy Unit of Work

## Goal

Implement a SQLAlchemy-backed `UnitOfWorkContract` that coordinates all SQLAlchemy repositories within a single database transaction.

The Unit of Work shall become the single owner of:

- SQLAlchemy Session lifecycle;
- transaction boundaries;
- commit;
- rollback.

Repositories must remain transaction-agnostic.

## Acceptance Criteria

- SQLAlchemyUnitOfWork implements UnitOfWorkContract.
- One Session shared across repositories.
- Session created in __enter__().
- Session closed in __exit__().
- Commit owned exclusively by UnitOfWork.
- Rollback owned exclusively by UnitOfWork.
- Automatic rollback without commit.
- Automatic rollback on exception.
- Repositories never commit or rollback.
- Shared transaction across repositories verified.
- Update + history rollback verified.
- Existing repository behavior unchanged.
- Existing tests pass.
- PostgreSQL integration tests pass.
- Ruff passes.
- Import validation passes.
- Architecture tests pass.
