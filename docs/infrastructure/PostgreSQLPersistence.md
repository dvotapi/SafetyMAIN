# PostgreSQL Persistence

SafetyMAIN Core uses synchronous SQLAlchemy 2.x for the PostgreSQL persistence foundation.

Synchronous SQLAlchemy was selected because the current application contracts and Unit of Work protocol are synchronous.

## Configuration

Required environment variable:

```bash
DATABASE_URL=postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain
```

Use `.env.example` as the local development template. Do not commit a real `.env` file.

## Local PostgreSQL

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Stop PostgreSQL:

```bash
docker compose down
```

## Migrations

Apply migrations:

```bash
DATABASE_URL=postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain python3 -m alembic upgrade head
```

Downgrade all migrations:

```bash
DATABASE_URL=postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain python3 -m alembic downgrade base
```

## Persistence Models

SQLAlchemy models live under:

```text
backend/core/infrastructure/persistence/sqlalchemy/models/
```

Domain entities do not inherit from SQLAlchemy classes. Future repository adapters will map between domain entities and persistence models.

## Repository Adapter

The SQLAlchemy Knowledge Object repository lives under:

```text
backend/core/infrastructure/persistence/sqlalchemy/repositories/
```

Mapping helpers live under:

```text
backend/core/infrastructure/persistence/sqlalchemy/mappers/
```

The repository receives an existing SQLAlchemy `Session`. It never creates engines, creates sessions, commits, rolls back, or closes the session. Transaction ownership belongs to the future SQLAlchemy Unit of Work.

The SQLAlchemy Knowledge Object Relation repository is implemented in the same repository package and persists directed relations from the existing relation repository contract.

## SQLAlchemy Unit of Work

`SQLAlchemyUnitOfWork` lives in:

```text
backend/core/infrastructure/persistence/sqlalchemy/unit_of_work.py
```

It receives a `sessionmaker` and creates a `Session` only in `__enter__()`. The same Session is shared by the Knowledge Object repository and Relation repository.

Lifecycle:

1. `__enter__()` creates the Session and repositories.
2. Application code performs repository operations.
3. `commit()` commits the transaction.
4. `__exit__()` rolls back automatically if `commit()` was not called or an exception escaped.
5. `__exit__()` always closes the Session and never suppresses exceptions.

Commit policy:

- `commit()` is owned exclusively by the Unit of Work.
- repeated `commit()` calls are no-ops, so no accidental empty transaction is committed.

Rollback policy:

- `rollback()` is owned exclusively by the Unit of Work.
- repeated `rollback()` calls are safe.

One Unit of Work instance is intended for one transaction. Nested Unit of Work and SAVEPOINT support are out of scope.

## Version History

`knowledge_objects` stores the current version.

`knowledge_object_versions` stores previous versions only. On update, the repository validates that the incoming version is exactly the persisted version plus one, appends the previous current row to history, and updates the current row.

The initial migration already includes a unique constraint on `knowledge_object_id + version`, so no additional migration was required for `TASK-P1-002`.

## Concurrency Preparation

The SQLAlchemy Knowledge Object repository loads the current row with a row lock during update and performs explicit version validation before writing history and replacing the current row.

This prevents silent version jumps in the adapter without introducing a full concurrency-control system.

## Search

Structured search is executed in PostgreSQL through SQLAlchemy expressions. Filtering supports organization, object type, lifecycle status, and exact top-level JSONB metadata equality.

Deleted Knowledge Objects are excluded by default and returned only when `status=DELETED` is requested explicitly.

## Relation Persistence

Directed relations are stored in `knowledge_object_relations`.

The SQLAlchemy relation repository:

- maps explicitly between `KnowledgeObjectRelation` and `KnowledgeObjectRelationModel`;
- never commits, rolls back, closes the session, or creates its own session;
- hard-deletes relation rows in `remove()`;
- always scopes traversal queries by `organization_id`;
- preserves reverse relations as distinct relations.

Duplicate relation IDs and duplicate directed relation identity both raise `DuplicateKnowledgeObjectRelation`. Self-reference is rejected with `SelfReferencingKnowledgeObjectRelation`.

Foreign-key failures are treated as unexpected integrity failures because normal application flow validates source and target Knowledge Objects before calling `add()`.

After any flush-time database integrity error, SQLAlchemy requires the transaction owner to roll back the session before reuse. Until the SQLAlchemy Unit of Work is implemented, callers/tests must perform that rollback externally.

## Contract Tests

Reusable contract suites live under:

```text
tests/contracts/
```

They verify observable behavior for:

- `KnowledgeObjectRepositoryContract`
- `KnowledgeObjectRelationRepositoryContract`
- `UnitOfWorkContract`

The same contract suites run against in-memory adapters during normal tests and against SQLAlchemy/PostgreSQL adapters when DB tests are enabled.

PostgreSQL DB tests are isolated by resetting the schema with Alembic downgrade/upgrade around each DB fixture. This is deterministic and simple, but may be optimized later.

## Current Scope

This foundation includes SQLAlchemy metadata, PostgreSQL table mappings, Alembic configuration, the initial migration, SQLAlchemy Knowledge Object repository, SQLAlchemy Relation repository and SQLAlchemy Unit of Work.

Production API integration is not implemented yet.

## Development Commands

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Apply migrations:

```bash
DATABASE_URL=postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain python3 -m alembic upgrade head
```

Run all non-DB tests:

```bash
python3 -m pytest
```

Run DB tests:

```bash
SAFETYMAIN_RUN_DB_TESTS=1 DATABASE_URL=postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain python3 -m pytest -m db
```

Run the complete suite with DB tests enabled:

```bash
SAFETYMAIN_RUN_DB_TESTS=1 DATABASE_URL=postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain python3 -m pytest
```

Downgrade migrations:

```bash
DATABASE_URL=postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain python3 -m alembic downgrade base
```

Re-apply migrations:

```bash
DATABASE_URL=postgresql+psycopg://safetymain:safetymain@localhost:5432/safetymain python3 -m alembic upgrade head
```

Stop PostgreSQL:

```bash
docker compose down
```

The normal test suite skips DB tests unless `SAFETYMAIN_RUN_DB_TESTS=1` is set.

If the local Docker installation does not include the Compose plugin, install Docker Compose support or start a compatible PostgreSQL instance manually and set `DATABASE_URL`.
