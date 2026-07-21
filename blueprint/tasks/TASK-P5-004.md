# TASK-P5-004 — Invitation Workflow

## Summary

Implemented invitation domain model, handlers, persistence, admin API, authenticated acceptance API, permissions, tests, and documentation.

## Decisions

- Acceptance requires an existing authenticated user with matching email.
- Effective expiration while persisted status remains `PENDING`.
- Token hashing via SHA-256; plaintext only on create/reissue.
- Default TTL: 7 days.
- Inactive memberships are reactivated on acceptance with invited role.

## Verification

Run:

```bash
ruff check .
pytest -q
```

PostgreSQL-backed tests:

```bash
SAFETYMAIN_RUN_DB_TESTS=1 DATABASE_URL=<postgresql-url> pytest -q
```

## Follow-up

- Email delivery integration
- Optional user provisioning if secure registration is added
