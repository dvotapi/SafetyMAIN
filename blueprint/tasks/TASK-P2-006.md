# TASK-P2-006

## Title

PostgreSQL Validation

## Status

Completed (2026-07-20)

## Summary

Validated the complete persistence layer against live PostgreSQL 17 and closed the Architecture Review v2 condition.

## Results

| Check | Result |
|-------|--------|
| Alembic upgrade/downgrade/re-upgrade | Pass |
| DB tests (`pytest -m db`) | 64 passed |
| Full suite with DB enabled | 371 passed |
| Readiness (live + unavailable) | Pass |
| HTTP smoke tests | Pass |
| Ruff | Pass |

## Persistence fixes during validation

- Shortened Alembic revision ID to fit `VARCHAR(32)`
- Relation repository `flush()` after `add()` for `exists()` contract
- UoW session cleanup after context exit
- `get_database_url({})` no longer falls back to `os.environ`
- Unified UoW tests on shared `db_fixtures`

## Decision

**READY FOR AUTHENTICATION FOUNDATION (P3-001)**

See [PostgreSQLValidation.md](../docs/persistence/PostgreSQLValidation.md).
