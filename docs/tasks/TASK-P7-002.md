# TASK-P7-002

## Title

Persistent Refresh Token Sessions and Rotation

## Status

Completed (2026-07-24)

## Summary

PostgreSQL is the production source of truth for refresh-token validity. Every login
creates a persistent refresh session; every successful refresh rotates `jti` atomically;
reuse revokes the session family; logout and user deactivation terminate refresh access
without persisting raw tokens.

## Deliverables

- [RefreshTokenSessions.md](../architecture/RefreshTokenSessions.md)
- Alembic revision `0009_refresh_token_sessions`
- Domain value objects / entity / repository contract
- SQLAlchemy + in-memory refresh session repositories
- Login session creation, refresh rotation, logout, deactivation revoke-all
- Taxonomy events: logout, refresh reuse, session revoked
- Cleanup script `scripts/cleanup_refresh_sessions.py`
- Architecture guardrails and concurrency/restart DB tests

## Verification

```bash
python -m pytest -m "not db" -q
SAFETYMAIN_RUN_DB_TESTS=1 python -m pytest -m db -q
python -m alembic heads
python scripts/cleanup_refresh_sessions.py --dry-run
```

## Next Step

Use session revocation hooks for future password-change and administrative session
management workflows. Access-token revocation remains a non-goal of this task.
