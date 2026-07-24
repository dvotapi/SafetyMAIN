# TASK-P6-003 — Authentication Security Events

Status: Complete  
Date: 2026-07-24

---

## Summary

Integrated the immutable security event taxonomy registry into the authentication
workflow so that login and refresh outcomes are recorded as structured, immutable
audit events without changing authentication HTTP contracts or weakening credential
and token security.

---

## Canonical Event Types

| Event type | Outcome |
|------------|---------|
| `authentication.login.succeeded` | SUCCESS |
| `authentication.login.failed` | FAILURE |
| `authentication.refresh.succeeded` | SUCCESS |
| `authentication.refresh.failed` | FAILURE |

Earlier taxonomy naming examples (`authentication.credential.rejected`,
`authentication.session.created`) were not published. The four identifiers above follow
the preferred `<category>.<subject>.<action>` convention and map directly to
authentication outcomes.

---

## Implementation

- Taxonomy family: `backend/core/domain/security_events/families/authentication.py`
- Recorder: `backend/core/application/audit/authentication_security_event_recorder.py`
- API boundary helper: `backend/api/authentication_audit.py`
- Handlers: `AuthenticateUserHandler`, `RefreshAuthenticationHandler`
- DI: `get_authentication_security_event_recorder()`
- JWT validation reasons on `TokenValidationError.reason` for normalized refresh audit codes

Reliability policy: authentication remains the primary operation; audit persistence uses a
separate Unit of Work for both success and failure; audit write failures are logged and
do not alter public authentication outcomes.

---

## Documentation

- Created `docs/architecture/AuthenticationSecurityEvents.md`
- Updated `SecurityEventTaxonomy.md`, `AuthenticationArchitecture.md`,
  `AdministrativeAuditLog.md`, `SecurityArchitectureReview.md`

---

## Tests

- `tests/core/test_authentication_security_event_recorder.py`
- Extended `tests/core/test_authentication_handlers.py`
- Extended `tests/api/test_authentication_api.py`
- `tests/api/test_authentication_sensitive_data.py`
- Registry/architecture coverage for authentication descriptors

---

## Verification

```bash
python -m pytest -q
python -m ruff check backend tests
```

---

## Deviations

- Documentation lives under `docs/architecture/` (no `docs/security/` tree in this repo).
- Unit recorder tests live under `tests/core/` (no `tests/unit/` tree).
- Authentication events without organization context are persisted but not listed by the
  current tenant-scoped Admin Audit API.
