# TASK-P5-005 — Administrative Audit Log

Status: Complete  
Date: 2026-07-21

---

## Summary

Introduced append-only administrative audit logging for User, Organization, Membership,
and Invitation workflows, plus a read-only scoped audit query API.

---

## Audit Model

Immutable `AuditEvent` domain entity with actor, authorization organization, target
organization, action, resource type/id, outcome, failure code, allowlisted metadata,
and `occurred_at`.

---

## Action Taxonomy

Centralized `AuditAction` enum (`user.create`, `organization.deactivate`,
`invitation.accept`, …) and `AuditResourceType` (`USER`, `ORGANIZATION`,
`MEMBERSHIP`, `INVITATION`).

---

## Transaction Decisions

- **Success:** business mutation and success audit event are staged in the same Unit
  of Work and committed atomically (`record_success()` then `commit()`). Commit failure
  triggers rollback of both.
- **Expected failure:** business Unit of Work rolls back first; failure audit is
  persisted in a separate audit transaction because the rolled-back transaction cannot
  store the failure event.
- **Failure-audit persistence error:** original business/API error preserved; safe log
  emitted.

---

## Failure-Audit Strategy

`AUDITABLE_ADMIN_FAILURES` maps known domain exceptions to stable failure codes.
Raw exception text, request bodies, and secrets are excluded.

---

## Query Scoping

Audit reads scoped from `TenantContext.organization_id` to events where
`authorization_organization_id` or `target_organization_id` matches. Out-of-scope
IDs return `404`.

---

## Metadata Rules

Allowlisted keys only (`changed_fields`, role/status transitions, `expiration_refreshed`,
`membership_id`). No entity snapshots or token material.

---

## Permissions

- Added `audit:read` (`SystemPermission.AUDIT_READ`)
- Granted to `admin` and `auditor`
- No public `audit:write`

---

## Persistence

- Table: `audit_events`
- Migration: `0005_audit_events` (`down_revision = 0004_invitations`)
- In-memory and SQLAlchemy repositories (append/get/list only)
- UnitOfWork exposes `audit_events`

---

## Integrated Operations

Audit integrated in application handlers via `AdministrativeAuditRecorder` and
`run_audited_admin_operation` for:

- user create/update/activate/deactivate
- organization create/update/activate/deactivate
- membership create/role change/activate/deactivate
- invitation create/revoke/reissue/accept

API routers pass `AuditContext.from_tenant()` or authenticated-user context for acceptance.

---

## API

Read-only endpoints:

- `GET /api/v1/admin/audit-events`
- `GET /api/v1/admin/audit-events/{audit_event_id}`

---

## Tests

- Domain: `tests/core/test_audit_event_domain.py`
- Recorder/UoW: `tests/core/test_administrative_audit_recorder.py`
- Repository contracts: in-memory + SQLAlchemy
- API/auth/scoping/sensitive data: `tests/api/test_admin_audit_events_api.py`
- Architecture guardrails: `tests/architecture/test_audit_guardrails.py`
- Updated existing admin handler/API tests for audit dependencies

---

## Documentation

- `docs/architecture/AdministrativeAuditLog.md`
- `docs/api/AdminAuditAPI.md`
- Updated P5 architecture/API cross-references

---

## Verification

```bash
python3 -m pytest -q
python3 -m ruff check .
```

PostgreSQL-backed verification:

```bash
SAFETYMAIN_RUN_DB_TESTS=1 DATABASE_URL=<postgresql-url> python3 -m pytest -q
```

Migration chain: `0001 → 0002 → 0003 → 0004 → 0005`.

---

## Known Limitations

- Permission-denied auditing in `require_permission()` deferred
- No platform-wide audit super-admin view
- No retention/export/streaming/signing

---

## Recommended Follow-Up

- Permission-denial audit policy integrated into authorization middleware
- Retention and export tooling
- Platform administrator role for cross-organization audit (separate task)
