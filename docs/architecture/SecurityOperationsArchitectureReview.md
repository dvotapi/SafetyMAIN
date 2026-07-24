# Security Operations Architecture Review

Status: Active  
Date: 2026-07-24  
Task: TASK-P6-006  
Final decision: **READY WITH CONDITIONS**

Related documents:

- [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md)
- [AdministrativeAuditLog.md](AdministrativeAuditLog.md)
- [AuthenticationSecurityEvents.md](AuthenticationSecurityEvents.md)
- [SecurityEventInvestigation.md](SecurityEventInvestigation.md)
- [AuditEventIntegrity.md](AuditEventIntegrity.md)
- [SecurityArchitectureReview.md](SecurityArchitectureReview.md)
- [PersistentIdentityStores.md](PersistentIdentityStores.md)

---

## 1. Executive Summary

Phase P6 is a coherent security-operations subsystem: taxonomy-backed immutable events,
tenant-isolated investigation, and tamper-evident per-organization integrity chains.

This review executed PostgreSQL-marked tests with `SAFETYMAIN_RUN_DB_TESTS=1`, closed
integrity verification gaps (chain-head mismatch, hash-link ordering under concurrency),
added architecture guardrails, CI for DB tests, and fail-hard DB fixture behavior.

**Decision: READY WITH CONDITIONS** — architecture and mandatory DB proofs are green;
remaining conditions are operational rollout items, not correctness blockers.

---

## 2. Scope

Validated:

- taxonomy registry and event families;
- administrative and authentication recorders;
- investigation API;
- integrity canonicalization / hashing / verification;
- PostgreSQL concurrency and migrations `0006` / `0007`;
- CLI verification;
- authorization (`audit:read`) and tenant isolation;
- sensitive-data boundaries.

Non-goals remain unchanged (signatures, SIEM, retention, lockout, etc.).

---

## 3. Component Inventory

| Component | Path / type | Layer | Responsibility |
|-----------|-------------|-------|----------------|
| Taxonomy registry | `backend/core/domain/security_events/registry.py` | Domain | Immutable event descriptors |
| Event families | `.../security_events/families/*.py` | Domain | Canonical names, category, severity |
| `AuditAction` | `backend/core/domain/value_objects/audit_action.py` | Domain | Stable action enum aligned to taxonomy |
| `AuditEvent` | `backend/core/domain/entities/audit_event.py` | Domain | Immutable event + allowlisted metadata |
| Canonicalizer | `.../services/audit_event_canonicalizer.py` | Domain | Deterministic payload bytes |
| Integrity service | `.../services/audit_integrity_service.py` | Domain | Finalize + verify (hash-link order) |
| Chain head VO | `.../value_objects/audit_chain_head.py` | Domain | Head state + advisory lock key text |
| Admin recorder | `.../application/audit/administrative_audit_recorder.py` | Application | Lifecycle + denial events |
| Auth recorder | `.../application/audit/authentication_security_event_recorder.py` | Application | Login/refresh/logout/session events |
| Auth context API | `backend/api/authentication_audit.py` | API | Safe request metadata extraction |
| Investigation query | `.../handlers/list_audit_events.py` | Application | Tenant-scoped filters |
| Integrity query | `.../handlers/verify_audit_chain.py` | Application | Chain + head verification |
| Repositories | in-memory + SQLAlchemy `audit_event_repository.py` | Infrastructure | Shared integrity append boundary |
| Models | `.../models/audit_event_model.py` | Infrastructure | `audit_events`, `audit_chain_heads` |
| API | `backend/api/routers/admin_audit_events.py` | API | List / get / integrity |
| CLI | `scripts/verify_audit_integrity.py` | Ops | All-organization verification |
| Migrations | `alembic/versions/0006_*`, `0007_*` | Persistence | Indexes + integrity backfill |
| Guardrails | `tests/architecture/test_p6_integrity_guardrails.py` | Tests | Bypass / taxonomy / lock key |

Persistence boundary: only `AuditEventRepository.add` finalizes integrity and updates the
chain head. Recorders construct drafts; they do not hash.

---

## 4. Security Event Write-Path Matrix

| Operation | Event name | Recorder | Actor | Organization | Failure policy | Integrity | Tests |
|-----------|------------|----------|-------|--------------|----------------|-----------|-------|
| User/org/membership/invitation lifecycle success | `*.create|update|...` | `AdministrativeAuditRecorder.record_success` | Tenant actor | Auth org (+ target) | Same UoW as mutation; failure fails business commit | Via repo `add` | admin audit API / handlers |
| Known admin failure | same action | `record_known_failure` / `record_failure` | Actor when known | Auth org | Separate UoW; best-effort; logged | Via repo `add` | admin failure tests |
| Permission denial | `authorization.permission_denied` | `record_permission_denial` | Authenticated actor | Tenant org | Separate UoW; best-effort | Via repo `add` | permission denial API |
| Login success/failure | `authentication.login.*` | `AuthenticationSecurityEventRecorder` | Trusted user or none | Optional org / else platform chain | Separate UoW; never fails auth | Via repo `add` | auth API / recorder |
| Refresh success/failure | `authentication.refresh.succeeded` / `.failed` | same | Success: trusted subject; failure: no actor | Optional / platform | Separate UoW; never fails refresh | Via repo `add` | auth refresh tests |
| Refresh reuse | `authentication.refresh.reused` | same | Session subject | Optional / platform | Revoke family then record | Via repo `add` | refresh reuse tests |
| Logout | `authentication.logout.succeeded` | same | Current-session logout may include actor | Optional / platform | Separate UoW; always 204 | Via repo `add` | logout API tests |
| Session revoked | `authentication.session.revoked` | same | Target user | Optional / platform | With deactivation UoW when bulk-revoking | Via repo `add` | deactivation revoke tests |
| Integrity verification | n/a | Handler only | n/a | Tenant | Read-only; no audit write on failure | Verifies chain+head | integrity API / CLI |

---

## 5. Read and Investigation Flow

`GET /api/v1/admin/audit-events` remains the investigation surface (`audit:read`,
tenant-scoped). Filters (event_name, category, severity, request_id, actor, outcome,
action, resource_type, time range) are unchanged. Integrity fields are additive.

`GET /api/v1/admin/audit-events/integrity` verifies the active tenant organization only.

---

## 6. Integrity Architecture

- Algorithm v1: SHA-256 over canonical JSON including `integrity_version` and
  `previous_integrity_hash` (explicit JSON null for genesis).
- Partition: authorization org → else target org → else platform sentinel.
- Verification orders events by **hash links**, not solely by `occurred_at`, so concurrent
  writers with inverted timestamps do not false-fail.
- Chain head must match the hash-link tail (`chain_head_mismatch`); empty events with a
  head, or events without a head, are invalid.
- Topology breaks (middle deletion, second genesis, fork) report `chain_fork`.

Term of art: **tamper-evident**, not tamper-proof.

---

## 7. Transaction Semantics

| Scenario | Behavior |
|----------|----------|
| Business mutation + admin success audit | Same UoW; atomic with mutation |
| Auth outcome + auth audit | Separate UoW; auth result independent |
| Event + integrity + chain head | Same repository transaction; advisory lock then FOR UPDATE |
| Rollback | Neither event nor head persists |
| Migration backfill | Single upgrade transaction populates hashes + heads |

---

## 8. Tenant Isolation / Authorization

- Investigation and integrity endpoints require Bearer + `X-Organization-ID` + `audit:read`.
- Clients cannot select another organization.
- Cross-org events are out of scope / masked as not found.
- Org-less auth events live on the platform chain and are not listed in tenant investigation.

---

## 9. Sensitive-Data Review

Allowlisted metadata only. Authentication context strips/normalizes request_id, client_ip,
user_agent. Sentinels remain confined to dedicated tests. Integrity API/CLI/logs omit
canonical payloads and credentials.

---

## 10. Concurrency Review

Lock key: `organization_advisory_lock_key_text(org)` → UUID string →
`pg_advisory_xact_lock(hashtext(...))`. Not Python `hash()`.

Why both advisory lock and `SELECT … FOR UPDATE`:

- advisory lock serializes genesis when no head row exists;
- row lock serializes updates once the head exists;
- both release on transaction end.

Proven by PostgreSQL concurrent same-org and cross-org tests.

---

## 11. Migration Review

`0007_audit_event_integrity_chain`:

- loads events ordered by `(occurred_at, id)`;
- uses runtime `AuditIntegrityService` for backfill;
- synchronous full-table approach suitable for small/medium DBs;
- **large production tables** should stage nullable → online backfill → NOT NULL
  (documented condition);
- downgrade is destructive.

Determinism verified against fixed IDs matching runtime algorithm.

---

## 12. Operational Tooling

```bash
DATABASE_URL=... python scripts/verify_audit_integrity.py
```

Exit `0` all valid; `1` integrity failure; `2` infrastructure error. No secrets/metadata dumps.

CI: `.github/workflows/postgresql-tests.yml` runs `-m db` with
`SAFETYMAIN_RUN_DB_TESTS=1` and fails if DB tests skip.

Local DB fixture fails hard when DB tests are requested without `DATABASE_URL` or
connectivity.

---

## 13. Test Coverage Matrix

| Area | Coverage |
|------|----------|
| Taxonomy / metadata / sentinels | Unit + API |
| Auth success/failure privacy | API + recorder |
| Investigation filters / tenant / authz | API |
| Canonicalization + known SHA-256 vectors | Unit |
| Chain verify + head mismatch + fork | Unit |
| Runtime append integrity | Contract + API |
| Same/cross-org concurrency | PostgreSQL |
| Migration backfill determinism | PostgreSQL |
| Tampering / rollback | PostgreSQL |
| CLI exit codes | PostgreSQL |
| Architecture bypass guardrails | Architecture tests |
| Fail-hard DB enablement | Unit fixture test |

---

## 14. Findings

### Resolved (Critical / High)

1. **Chain-head not verified** → verifier + handler/CLI compare head to hash-link tail.
2. **Concurrent timestamp inversion false-failed chains** → verify by integrity links;
   documented presentation-order ≠ chain order.
3. **DB tests silently skippable under `SAFETYMAIN_RUN_DB_TESTS=1`** → fail hard.
4. **No CI DB job** → GitHub Actions PostgreSQL workflow added.
5. **Invitation/membership SQLAlchemy contracts violated FKs when DB tests ran** →
   seeding adapters for contract fixtures (latent pre-P6 debt blocking P6 closeout).
6. **Integrity bypass / taxonomy drift risk** → architecture guardrails.

### Remaining conditions (Medium / Ops)

1. Schedule periodic `verify_audit_integrity.py` in operations.
2. For very large audit tables, replace synchronous `0007` backfill with staged rollout.
3. Future: external anchoring / signatures (explicit non-goals now).
4. Confirm CI workflow green on first GitHub Actions run in the target repository.
5. ~~Persistent identity/membership as production source of truth~~ — closed by
   [TASK-P7-001](../tasks/TASK-P7-001.md) / [PersistentIdentityStores.md](PersistentIdentityStores.md).
8. Refresh-token sessions and rotation are production requirements —
   [TASK-P7-002](../tasks/TASK-P7-002.md) / [RefreshTokenSessions.md](RefreshTokenSessions.md).

---

## 15. Final Decision

**READY WITH CONDITIONS**

All non-DB and required PostgreSQL tests executed and passed in this review environment:

```text
pytest -m "not db"  → 670 passed
SAFETYMAIN_RUN_DB_TESTS=1 pytest -m db → 93 passed
Alembic head → 0007_audit_event_integrity_chain
```

No unresolved Critical or High correctness findings remain.
