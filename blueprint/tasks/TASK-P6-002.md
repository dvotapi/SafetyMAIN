# TASK-P6-002 — Security Event Taxonomy & Registry

Status: Complete  
Date: 2026-07-24

---

## Summary

Introduced a centralized immutable Security Event Taxonomy Registry describing all
currently published persisted security-relevant audit event types without changing
runtime audit behavior, persistence schema, Audit API contracts, or P6-001 authorization
guardrails.

---

## Implementation

Domain module:

```text
backend/core/domain/security_events/
```

Components:

- typed primary categories (`SecurityEventCategory`);
- typed subject domains (`SecurityEventSubjectDomain`);
- typed producer owners (`SecurityEventProducerOwner`);
- optional significance (`SecurityEventSignificance`);
- immutable `SecurityEventDescriptor`;
- family modules for administrative and authorization events;
- centralized `SECURITY_EVENT_REGISTRY`;
- registry and naming validation.

---

## Current Event Inventory

Seventeen published event types registered — one-to-one with `AuditAction`:

- sixteen Administrative Audit actions (`ADMINISTRATIVE` / `ADMINISTRATIVE_AUDIT`);
- `authorization.permission_denied` (`AUTHORIZATION` / `AUTHORIZATION`, subject
  `SECURITY_SYSTEM`, outcomes `FAILURE` only).

No identifiers were renamed. All current identifiers are marked `legacy_identifier=True`
because they predate the preferred `<category>.<subject>.<action>` convention.

---

## Architectural Decisions

| Decision | Choice |
|----------|--------|
| Persistence | No schema or migration changes |
| Runtime integration | Registry is metadata only; no recorder redesign |
| Resource type | Persisted `AuditResourceType` unchanged; taxonomy uses separate `subject_domain` |
| Significance | Optional registry metadata only; assigned to `authorization.permission_denied` |
| Validation | Registry validated at import via `validate_security_event_registry()` |
| Naming | Preferred 3-segment convention enforced for new identifiers; legacy flag for current |

---

## Producer Mappings

| Event family | Trigger owner | Producer owner | Recorder |
|--------------|---------------|----------------|----------|
| Administrative Audit | `run_audited_admin_operation()` / handler boundary | `ADMINISTRATIVE_AUDIT` | `AdministrativeAuditRecorder` |
| Authorization Permission Denial | `require_permission()` | `AUTHORIZATION` | `AdministrativeAuditRecorder.record_permission_denial()` |

---

## Compatibility Guarantees

Unchanged:

- `AuditEvent` persistence schema;
- Administrative Audit success/failure transaction behavior;
- Authorization Permission Denial production semantics;
- Audit API schemas, filters, and tenant scoping;
- RBAC and compatibility mode;
- P6-001 anti-duplication guardrails.

---

## Guardrails Added

- `tests/core/test_security_event_registry.py` — descriptor and registry validation;
- `tests/architecture/test_security_event_taxonomy.py` — dependency direction, completeness,
  producer ownership, centralized authorization production;
- existing P6-001 guardrails preserved unchanged.

---

## Documentation

- Created `docs/architecture/SecurityEventTaxonomy.md`;
- updated `AdministrativeAuditLog.md`, `AuthorizationFoundation.md`,
  `RoleBasedAuthorization.md`, `AuthenticationArchitecture.md`,
  `SecurityArchitectureReview.md`.

---

## Files Changed

```text
backend/core/domain/security_events/
tests/core/test_security_event_registry.py
tests/architecture/test_security_event_taxonomy.py
docs/architecture/SecurityEventTaxonomy.md
docs/architecture/AdministrativeAuditLog.md
docs/architecture/AuthorizationFoundation.md
docs/architecture/RoleBasedAuthorization.md
docs/architecture/AuthenticationArchitecture.md
docs/architecture/SecurityArchitectureReview.md
blueprint/tasks/TASK-P6-002.md
```

---

## Verification

```bash
ruff check .
pytest -q tests/core/test_security_event_registry.py tests/architecture/test_security_event_taxonomy.py
pytest -q tests/architecture/test_audit_guardrails.py tests/api/test_permission_denial_audit_api.py
pytest -q
```

---

## Deferred Work

- TASK-P6-003 — Authentication Security Events production and persistence;
- TASK-P6-004 — Audit Retention & Lifecycle;
- TASK-P6-005 — Audit Export API;
- TASK-P6-006 — Audit Integrity;
- runtime registry lookup integration in recorders (not required for P6-002);
- persisted category/subject/significance columns.

---

## Deviations

None. No runtime behavior changes were required beyond introducing taxonomy metadata and
validation tests.
