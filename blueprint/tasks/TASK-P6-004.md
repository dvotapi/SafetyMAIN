# TASK-P6-004 — Security Event Query and Investigation API

Status: Complete  
Date: 2026-07-24

---

## Summary

Extended the existing administrative audit list endpoint into a taxonomy-aware security
event investigation interface with registry-validated filters, request correlation,
half-open time bounds, repository-side filtering/counting, and investigation indexes.

---

## Key Decisions

| Topic | Choice |
|-------|--------|
| Storage | Reuse `audit_events`; no parallel store |
| Category / severity filters | Expand via immutable taxonomy registry to `action IN (...)` |
| Severity authority | Registry `default_security_significance` (not derived from outcome) |
| Request ID | Exact match on allowlisted metadata key |
| Time bounds | `occurred_from <= occurred_at < occurred_to` |
| Route | Preserve `GET /api/v1/admin/audit-events` |
| Auth events visibility | Tenant-scoped; org-less auth events remain out of tenant list scope |

---

## Implementation

- `backend/core/domain/security_events/query_resolution.py`
- Extended `AuditEventListCriteria`, `ListAuditEventsQuery`, handler
- API params: `backend/api/params/audit_event_investigation.py`
- Response enrichment: `event_name`, `event_category`, `severity`, `request_id`
- SQLAlchemy DB-side predicates, count, order, limit/offset
- In-memory repository parity
- Alembic `0006_audit_investigation_indexes`

---

## Documentation

- Created `docs/architecture/SecurityEventInvestigation.md`
- Updated Admin Audit API / taxonomy / authentication security events docs as needed

---

## Verification

```bash
python -m pytest -q
python -m ruff check <changed files>
```
