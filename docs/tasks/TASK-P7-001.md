# TASK-P7-001

## Title

Persistent Identity and Membership Stores

## Status

Completed (2026-07-24)

## Summary

Closed remaining production rollout conditions for identity persistence: PostgreSQL is
the authoritative source of truth for users, organizations, and memberships in
production. Constraint races map to domain exceptions, membership role CHECK is
enforced in Alembic `0008`, in-memory uniqueness matches PostgreSQL semantics for
tests, and architecture guardrails prevent silent production in-memory fallbacks.

## Deliverables

- [PersistentIdentityStores.md](../architecture/PersistentIdentityStores.md)
- Alembic revision `0008_membership_role_check`
- IntegrityError mapping in `identity_constraint_errors.py`
- In-memory uniqueness parity for users and memberships
- Production container hardening against in-memory identity injection
- Contract, concurrency, restart, and architecture guardrail tests

## Verification

```bash
python -m pytest -m "not db" -q
SAFETYMAIN_RUN_DB_TESTS=1 python -m pytest -m db -q
python -m alembic heads
```

## Next Step

Operate production with `DATABASE_URL`, seed identity explicitly where required, and
keep periodic audit integrity verification from P6.
