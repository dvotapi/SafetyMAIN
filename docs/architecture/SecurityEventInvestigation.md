# Security Event Investigation

Status: Active  
Date: 2026-07-24  
Task: TASK-P6-004

Related documents:

- [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md)
- [AuthenticationSecurityEvents.md](AuthenticationSecurityEvents.md)
- [AdministrativeAuditLog.md](AdministrativeAuditLog.md)
- [AuditEventIntegrity.md](AuditEventIntegrity.md)
- [SecurityOperationsArchitectureReview.md](SecurityOperationsArchitectureReview.md)
- [AdminAuditAPI.md](../api/AdminAuditAPI.md)

---

## 1. Purpose

Authorized administrators and auditors investigate immutable, taxonomy-backed security
events through the existing administrative audit list endpoint.

Typical questions:

- Which login attempts failed in this period?
- Which events share this request ID?
- Which authentication failures affected this actor?
- Which medium-significance events occurred in this organization?
- Which permission denials occurred near an authentication failure?

The immutable `audit_events` store remains the single source of truth. This task extends
query capability; it does not introduce a parallel security-event database.

---

## 2. Endpoints

```text
GET /api/v1/admin/audit-events
GET /api/v1/admin/audit-events/integrity
GET /api/v1/admin/audit-events/{audit_event_id}
```

Permission: `audit:read`

Integrity verification is read-only, tenant-scoped, and documented in
[AuditEventIntegrity.md](AuditEventIntegrity.md). List/detail responses expose
`integrity_hash`, `previous_integrity_hash`, and `integrity_version` to authorized
readers.  
Tenant scope: trusted `X-Organization-ID` / tenant context  
Operation ID: `list_audit_events` (unchanged)

---

## 3. Supported Filters

All supplied filters use logical **AND** and exact matching.

| Parameter | Semantics |
|-----------|-----------|
| `event_name` | Canonical taxonomy event name; validated via registry before repository access |
| `event_category` | `SecurityEventCategory` (`ADMINISTRATIVE`, `AUTHENTICATION`, `AUTHORIZATION`, `SECURITY_INFRASTRUCTURE`) |
| `severity` | Registry `SecurityEventSignificance` (`INFORMATIONAL`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) |
| `action` | Existing `AuditAction` filter |
| `outcome` | `SUCCESS` / `FAILURE` |
| `resource_type` | Existing resource type enum including `SESSION` |
| `actor_user_id` | Actor UUID |
| `request_id` | Exact metadata request ID |
| `occurred_from` | Inclusive lower bound (`occurred_at >= from`) |
| `occurred_to` | Exclusive upper bound (`occurred_at < to`) |
| `target_organization_id` | Existing target-org filter within tenant scope |
| `offset` / `limit` | Pagination (default 0 / 20, max 100) |
| `sort_ascending` | Default `false` |

Unknown taxonomy `event_name` values are rejected with `422 request_validation_error`.
They are never treated as an empty-result filter.

---

## 4. Taxonomy Resolution

`event_category` and `severity` are **not persisted columns**. They are authoritative
static registry metadata (`SecurityEventDescriptor`).

Query resolution expands category/severity into an `action IN (...)` predicate using the
immutable registry. This is not severity derivation from outcome.

Response projection:

- `event_name` = persisted `action`
- `event_category` = registry category for that action
- `severity` = registry `default_security_significance` when present
- `request_id` = allowlisted metadata value when present

---

## 5. Tenant Isolation

Every list query is constrained to:

```text
authorization_organization_id = tenant
OR target_organization_id = tenant
```

Client-supplied organization identifiers cannot broaden access. Identical `request_id`
values across organizations do not allow cross-tenant discovery.

Authentication events without organization context remain persisted but are not visible
through this tenant-scoped endpoint unless an organization ID was recorded on the event.

---

## 6. Ordering and Pagination

Default ordering:

```text
occurred_at DESC, audit_event_id DESC
```

Ascending mode reverses both keys. Equal timestamps remain deterministic via event ID.

Filtered `total` uses the same predicates as the page query.

---

## 7. Metadata Safety

Allowlisted metadata and existing redaction rules remain authoritative. Investigation
responses must not expose passwords, hashes, tokens, authorization headers, JWT material,
secrets, stack traces, or raw authentication exception text.

Arbitrary metadata-key search is out of scope.

---

## 8. Index Rationale

Migration `0006_audit_investigation_indexes` adds:

| Index | Why |
|-------|-----|
| `(authorization_organization_id, occurred_at)` | Mandatory tenant + timeline access path |
| `(target_organization_id, occurred_at)` | Target-scoped events in the same list semantics |
| `(action, occurred_at)` | Event-name / category-expanded action filters |
| `(actor_user_id, occurred_at)` | Actor investigation timelines |
| expression `(metadata->>'request_id')` where present | Exact request correlation without a new column |

Category/severity columns were intentionally not added in this task.

---

## 9. Example

```http
GET /api/v1/admin/audit-events
  ?event_category=AUTHENTICATION
  &outcome=FAILURE
  &request_id=req-123
  &occurred_from=2026-07-01T00:00:00Z
  &occurred_to=2026-08-01T00:00:00Z
```

---

## 10. Known Limitations

- No OR expressions, regex, full-text, or arbitrary metadata predicates.
- No cursor pagination.
- No platform-wide cross-organization investigation view for ordinary org admins.
- Registry significance is static metadata; historical rows reflect current registry mapping
  at read time until persisted significance columns exist (future work).
