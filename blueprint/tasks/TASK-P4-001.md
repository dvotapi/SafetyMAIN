# TASK-P4-001

## Title

Identity Persistence

## Status

Completed (2026-07-21)

## Summary

Replaced temporary in-memory identity and membership adapters with SQLAlchemy
persistence for users, organizations, and memberships while preserving existing
authentication and authorization behavior.

## Deliverables

- [IdentityPersistence.md](../docs/architecture/IdentityPersistence.md)
- Alembic migration `0002_identity_persistence`
- `backend/bootstrap/seed_identity.py`

## Verification

- Existing test suite passes
- Identity repository contract tests pass
- Alembic metadata tests updated
- PostgreSQL contract tests available with `SAFETYMAIN_RUN_DB_TESTS=1`

## Next Step

Apply identity persistence in deployment environments and retire compatibility-only
in-memory defaults where PostgreSQL is available.
