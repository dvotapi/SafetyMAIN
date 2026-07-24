# Audit Event Integrity

Status: Active  
Date: 2026-07-24  
Task: TASK-P6-005

Related documents:

- [AdministrativeAuditLog.md](AdministrativeAuditLog.md)
- [AuthenticationSecurityEvents.md](AuthenticationSecurityEvents.md)
- [SecurityEventInvestigation.md](SecurityEventInvestigation.md)
- [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md)
- [SecurityArchitectureReview.md](SecurityArchitectureReview.md)

---

## 1. Threat Model and Guarantee

The audit integrity chain makes unauthorized modification, deletion, insertion, or
reordering of persisted organization-scoped audit events **detectable**.

It does **not** independently prevent:

- a database administrator from rewriting an entire chain;
- an attacker with full application and database write access from recomputing hashes;
- deletion of an entire organization chain;
- rollback of the database to an earlier consistent snapshot.

This mechanism is **tamper evidence**, not a digital signature. No signing keys, HMAC
secrets, or asymmetric cryptography are introduced in TASK-P6-005.

A failed integrity verification is a security-relevant operational condition. This task
does **not** automatically append a new audit event for verification failure, because
writing into a potentially invalid chain can complicate investigation.

---

## 2. Per-Organization Hash Chain

Each audit event stores:

| Field | Semantics |
|-------|-----------|
| `previous_integrity_hash` | SHA-256 hex of the previous event in the same chain, or `null` for genesis |
| `integrity_hash` | SHA-256 hex of this event’s integrity commitment |
| `integrity_version` | Algorithm/version identifier (`1` currently) |

Chain partition key (preference order):

1. `authorization_organization_id`
2. else `target_organization_id`
3. else platform sentinel `00000000-0000-4000-8000-000000000001`

Org-less authentication events therefore share a platform chain. Tenant verification
endpoints only verify the active tenant organization chain.

Genesis: the first event in each chain has `previous_integrity_hash = null`. The
canonical payload still includes an explicit JSON `null` for the previous hash.

---

## 3. Canonical Serialization (v1)

Module: `backend/core/domain/services/audit_event_canonicalizer.py`

Rules:

- UTF-8 JSON
- sorted object keys
- separators `(",", ":")`
- `ensure_ascii=False`, `allow_nan=False`
- timezone-aware timestamps normalized to UTC with microsecond precision
  (`YYYY-MM-DDTHH:MM:SS.ffffffZ`)
- UUIDs as canonical string form
- metadata recursively normalized; unsupported / non-finite values rejected

Hash input conceptually:

```text
SHA-256(canonical_json({
  integrity_version,
  previous_integrity_hash,
  event: <canonical event payload including integrity_version>
}))
```

Integrity hash fields themselves are excluded from the event payload. Digest encoding is
lowercase hexadecimal (64 characters).

---

## 4. Integrity Versioning

Current version: `1` (`CURRENT_AUDIT_INTEGRITY_VERSION`).

Unknown versions fail verification with `unsupported_integrity_version` and are never
interpreted with the v1 algorithm.

Future versions may change canonical format, hash algorithm, introduce keyed MACs,
signatures, or external anchoring without silently reinterpreting historical rows.

---

## 5. Concurrency and Chain Heads

PostgreSQL appends serialize per chain organization using:

1. transaction-scoped `pg_advisory_xact_lock(hashtext(organization_id))`
2. `SELECT … FOR UPDATE` on `audit_chain_heads`
3. finalize hash → insert event → upsert chain head in the same transaction

Table `audit_chain_heads` (not exposed via public API):

- one row per chain organization
- `latest_audit_event_id`, `latest_integrity_hash`, `integrity_version`, `updated_at`

Tradeoff: same-organization writers serialize; different organizations use independent
locks and do not block each other via the advisory key.

In-memory repository uses a process-local `threading.RLock`. It does not reproduce
cross-process PostgreSQL locking.

---

## 6. Shared Persistence Boundary

Integrity finalization occurs inside `AuditEventRepository.add` for both SQLAlchemy and
in-memory implementations. All recorders (administrative and authentication) inherit the
behavior automatically.

Integrity calculation failures are audit recording failures: no partial event, no head
update without an event, no event without integrity fields. Failure logs must not dump
full metadata/canonical payloads.

---

## 7. Migration and Backfill

Alembic revision `0007_audit_event_integrity_chain` (after
`0006_audit_investigation_indexes`):

1. add nullable integrity columns + `audit_chain_heads`
2. backfill each chain partition in ascending `(occurred_at, id)` using the runtime
   canonical algorithm
3. enforce non-null `integrity_hash` / `integrity_version`

Production-scale note: synchronous full-table backfill in a single migration is
acceptable only for small datasets. Large deployments should stage nullable deploy →
online backfill → constraint enforcement.

Downgrade is **destructive**: integrity columns and chain heads are removed.

---

## 8. Verification

Application query: `VerifyAuditChainQuery`  
Handler: `VerifyAuditChainHandler`  
API: `GET /api/v1/admin/audit-events/integrity` (`audit:read`, tenant-scoped)

Response fields: `organization_id`, `valid`, `checked_event_count`,
`first_invalid_event_id`, `reason`.

Normalized reasons:

- `missing_integrity_hash`
- `invalid_integrity_hash_format`
- `previous_hash_mismatch`
- `event_hash_mismatch`
- `unsupported_integrity_version`
- `unexpected_genesis`
- `chain_head_mismatch`
- `chain_fork`

Verification reconstructs append order from integrity hash links (not presentation
order / `occurred_at` alone). Concurrent writers may produce inverted timestamps; the
hash-link topology remains authoritative. After event verification, the persisted
`audit_chain_heads` row must match the hash-link tail. Final-event deletion is detected
as `chain_head_mismatch`. Middle deletion / second genesis / forks report `chain_fork`.

Operational CLI: `python scripts/verify_audit_integrity.py`  
Exit `0` when all chains are valid; non-zero otherwise. Does not print credentials or
full metadata.

Phase P6 closeout: [SecurityOperationsArchitectureReview.md](SecurityOperationsArchitectureReview.md).

Investigation list/detail responses expose integrity fields to `audit:read` callers.
Genesis `previous_integrity_hash` is JSON `null`.

Memory characteristic: verification currently loads the full organization chain into
memory. Large chains may require batched iteration in a later task.

---

## 9. Sensitive Data

Canonicalization and verification operate only on already allowlisted audit metadata.
Passwords, password hashes, access/refresh tokens, Authorization headers, JWT material,
and application secrets must never enter the payload. Integrity failure logs include only
safe identifiers and normalized reasons.

---

## 10. Future Upgrade Paths

- keyed HMAC integrity
- asymmetric signatures / key management
- external hash anchoring / TSA
- scheduled integrity monitoring and SIEM export
- long-term retention policies
