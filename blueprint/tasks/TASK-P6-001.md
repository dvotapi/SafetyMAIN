# TASK-P6-001 — Permission Denial Administrative Auditing

Status: Complete  
Date: 2026-07-23

---

## Summary

Added secure administrative audit recording for authenticated permission-denied requests
that occur after trusted actor and authorization organization resolution, integrated
centrally in `require_permission()` without changing HTTP error semantics.

---

## Permission-Denial Audit Policy

An audit event is created only when:

- Bearer authentication and JWT validation succeeded;
- `SecurityContext` contains an active actor user;
- `TenantContext` resolved an authorization organization;
- active membership was verified by existing organization-access rules;
- permission evaluation denied a required **administrative** system permission.

Excluded: `401` authentication failures, `422` organization-context failures,
missing/inactive membership before permission evaluation, compatibility-mode anonymous
requests, and business permission denials.

---

## Action Taxonomy

- Action: `authorization.permission_denied` (`AuditAction.AUTHORIZATION_PERMISSION_DENIED`)
- Outcome: `FAILURE`
- Failure code: `permission_denied` (`PERMISSION_DENIED_FAILURE_CODE`)

---

## Resource Type Strategy

Resource type is mapped from the required permission via
`resource_type_for_permission()` (for example `audit:read` → `AUDIT_EVENT`,
`membership:write` → `MEMBERSHIP`). No URL parsing or handler-name inference.

---

## Integration Point

- API: `backend/api/dependencies.py` → `require_permission()`
- Spec builder: `backend/api/permission_denial_audit.py`
- Classification: `is_administrative_permission()` in
  `backend/core/application/audit/permission_denial_audit.py`
- Persistence: `AdministrativeAuditRecorder.record_permission_denial()`

Routers and the global exception mapper do not construct permission-denial events.

---

## Actor and Organization Requirements

- Actor: `SecurityContext.user_id` / `TenantContext.actor_user_id` only
- Authorization organization: `TenantContext.organization_id` only
- Target organization: optional path UUID (`organization_id`) when safely available
- Resource ID: optional path UUID (`user_id`, `membership_id`, `invitation_id`,
  `audit_event_id`) when safely available

---

## Metadata Allowlist

- `required_permission`
- `http_method`
- `route_template` (normalized to `/api/v1/...`)
- `operation_id` (optional)
- `target_identifier_present`
- `permission_category`

No JWT, Authorization header, request body, secrets, or raw exception text.

---

## Transaction Model

Permission denial uses a dedicated failure Unit of Work (`record_permission_denial()`).
No business mutation occurs. Audit persistence failure preserves `403 permission_denied`
and emits a safe operational log.

---

## Compatibility Mode

When `AUTH_ENFORCEMENT=false`, `require_permission()` remains a no-op and no
permission-denial audit events are created.

---

## Administrative vs Business Endpoint Policy

Administrative system permissions are audited. Business permissions (`knowledge_object:*`,
`relation:*`) are not written to the administrative audit log in this task.

---

## Duplicate Prevention

Exactly one `record_permission_denial()` attempt per denied request inside
`require_permission()`. Exception handlers do not duplicate auditing.

Architecture guardrail: each API route handler uses at most one
`require_permission()` dependency (`assert_at_most_one_require_permission_per_route_handler`).

---

## Persistence

Reuses existing `audit_events` table and append-only repository. No new migration.

---

## Tests

- `tests/core/test_permission_denial_audit.py`
- `tests/core/test_audit_event_domain.py` (permission-denial metadata/action)
- `tests/api/test_permission_denial_audit_api.py` (matrix, negatives, persistence failure,
  compatibility mode, audit API visibility, sensitive data)
- `tests/architecture/test_audit_guardrails.py` (centralized integration guardrails)

---

## Documentation Updates

- `docs/architecture/AdministrativeAuditLog.md`
- `docs/architecture/RoleBasedAuthorization.md`
- `docs/architecture/AuthorizationFoundation.md`
- `docs/architecture/SecurityArchitectureReview.md`
- `docs/api/AdminAuditAPI.md`

---

## Verification

```bash
ruff check .
pytest -q
```

PostgreSQL-backed tests (when configured):

```bash
SAFETYMAIN_RUN_DB_TESTS=1 DATABASE_URL=<postgresql-url> pytest -q
```

---

## Known Limitations

- Business endpoint permission denials are not administratively audited.
- Authentication events are not stored in the administrative audit table.
- No platform-wide cross-organization audit view.

---

## Recommended Follow-Up

- Business security-event auditing for Knowledge Object / Relation denials
- Authentication/session audit stream (separate from administrative audit log)
- Retention and export policies
