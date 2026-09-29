# ADR-0010 — Electronic Journals and Simple Electronic Signature

**Status:** Proposed

**Date:** 2026-09-14

**Authors:** SafetyMAIN Architecture Team

---

# Context

Safety journals are kept on paper today: briefing logs, PPE issue logs, knowledge-check logs, equipment inspection logs, and production-control logs. Employees confirm entries with a handwritten signature.

Epic P11 decides that journals are kept electronically, append-only, and signed by the employee with a simple electronic signature (ПЭП), governed by an internal regulation on electronic document flow. Every employee gets a minimal SafetyMAIN account.

The platform already has:

- a per-organization audit hash chain that makes modification, deletion, insertion, and reordering of audit events detectable, with the verification script `scripts/verify_audit_integrity.py` (`docs/architecture/AuditEventIntegrity.md`);
- role-based authorization: an active membership resolves a role, and the role grants permissions (`docs/architecture/RoleBasedAuthorization.md`);
- the roles `admin`, `member`, and `auditor`; no role limits a user to their own records.

The audit hash chain is tamper evidence, not a digital signature. It does not protect against a database administrator rewriting an entire chain (`AuditEventIntegrity.md` §1).

Employees come from `hr_form` through the read-model `Employee` (ADR-0008).

---

# Decision

A journal is an **append-only** electronic register.

The electronic register is the record. Paper forms are generated from it.

Employees confirm entries with a simple electronic signature from their own authenticated session.

---

# Journal Model

| Concept | Content |
|---|---|
| `Journal` | type, organisation unit, responsible, period, status |
| `JournalEntry` | schema-driven fields, subjects, author, created_at |

Append-only rules:

- The content of an entry — every attribute of its canonical payload — is never updated, and an entry is never deleted — not through the API, not in the application layer, not in repositories.
- A correction is a new entry of kind `reversal` that references the corrected entry.
- The corrected entry stays readable.
- A change of the journal status never changes its entries.

Journals and entries are Knowledge Objects (ADR-0002) and belong to an organization. Cross-organization access is reported as not found (404).

Exact fields, entry numbering, and reversal rules are specified by P11-005.

---

# Entry Schemas as Metadata

- Entry field schemas are metadata: the `JournalType` catalog (ADR-0003), not code.
- A new journal type or a changed field set is a metadata change.
- An entry is validated against the schema of its journal type when it is created.
- Schema changes follow Version Everything (Freeze §10): existing entries stay readable after a schema change.

---

# Integrity

Each journal entry is hashed into the existing audit hash chain.

- Every entry has a canonical payload, serialized with the rules of `AuditEventIntegrity.md` §3.
- Creating an entry records an audit event in the organization's audit hash chain. An entry is never persisted without its audit event.
- The audit event carries the SHA-256 of the canonical entry payload, not the payload itself. Entry content stays out of audit metadata (`AuditEventIntegrity.md` §9).
- Journals do not build a second hash chain.

Verification:

- `scripts/verify_audit_integrity.py` verifies the audit hash chain, as it does today.
- P11-005 extends the script to check journal records against the chain one to one:
  - every journal entry and every signature record has exactly one creation audit event, and the recomputed SHA-256 of the record equals the hash committed in that event;
  - every creation audit event of an entry or a signature record has its record.
- A modified, deleted, or directly inserted entry or signature record is therefore detected.

Limits, inherited from `AuditEventIntegrity.md` §1:

- tampering is detected, not prevented;
- a database administrator, or an attacker with full application and database write access, can rewrite and recompute the chain;
- deletion of an entire organization chain is not detected;
- a rollback of the whole database to an earlier consistent snapshot is not detected.

---

# Simple Electronic Signature (ПЭП)

Whether an entry requires signatures is defined by its journal type.

An entry that requires an employee's signature is `awaiting_signature` until the employee confirms it from their own authenticated session.

- Only the employee signs for themselves. Nobody signs on behalf of another person.
- The employee confirms the entry content that is shown to them.

The signature is a separate, append-only **signature record** (`JournalEntrySignature`). It stores at least:

- user id;
- timestamp;
- client IP;
- user agent;
- SHA-256 of the canonical entry payload.

Rules:

- Signing never changes the entry content. The canonical payload stays as it was created.
- The state of an entry — `awaiting_signature`, `signed`, `reversed`, and any later state — is derived from appended records: signature records, `reversal` entries, and future append-only records such as the cancellation of a required signature. For example, an entry is `signed` when every required signature record exists.
- How the derived state is stored for queries (a projection, or a column outside the canonical payload) is decided by P11-005. It is never part of the hashed entry payload.
- How a required signature is cancelled, for example on dismissal (ADR-0008), is decided by P11-005 and P11-011. The cancellation is itself an append-only record.
- A signature record is valid only when its SHA-256 equals the canonical hash of the entry it signs.
- A signature record is never updated or deleted. Creating it records an audit event that carries the SHA-256 of the canonical signature record payload, serialized with the same rules (`AuditEventIntegrity.md` §3), in the same way as entries.

Employee acknowledgements of documents, which the Obligations Engine tracks (ADR-0005), use the same signature record.

Enhanced and qualified electronic signatures are out of scope.

---

# Legal Basis

- The legal basis of ПЭП is an internal regulation on electronic document flow and simple electronic signature.
- Every employee acknowledges the regulation.
- The regulation is a `ComplianceDocument`: uploaded (P11-001) or assembled from Knowledge Blocks (ADR-0009, P11-003).

The audit hash chain provides integrity evidence for signed entries. It is not the signature. The signature rests on the regulation, its acknowledgement by the employee, and the signature record.

---

# Employee Access

- Every employee receives a minimal SafetyMAIN account with the role `employee` (epic P11; introduced by P11-004).
- The `employee` role can see and sign only the employee's own entries and acknowledgements.
- An entry is the employee's own when the signed-in user is linked to an employee who is a subject of the entry.

Role-based authorization answers whether a role may sign. It does not answer whether a record belongs to the caller. A subject check is therefore required in the application layer in addition to the permission check. Records of other employees are reported as not found (404).

---

# Printable Forms

- Printable forms mandated by regulation are generated artifacts of the electronic register (ADR-0001; Freeze §2).
- They are generated in the background worker (ADR-0007) and stored in object storage (ADR-0006).
- A printed form never replaces or changes the electronic record.
- Signature cells show that the entry was signed with ПЭП. The layout is specified by P11-005.

---

# Principles

- The electronic register is the record; paper is a generated view.
- Append, never rewrite.
- Corrections are visible entries.
- A signature is given only by the signer, from their own session.
- Integrity evidence reuses the audit hash chain.
- Journal structure is metadata.

---

# Consequences

- P11-005 introduces `Journal`, `JournalEntry`, `JournalEntrySignature`, the `JournalType` catalog, the signing flow, printable forms, and the extension of `scripts/verify_audit_integrity.py`.
- P11-004 introduces the `employee` role and links employees to user accounts (ADR-0008).
- Authorization gains a subject-level check for employee-owned records. The security matrix tests cover the `employee` role.
- An entry has exactly one version. The history of a journal is its sequence of entries and reversals (ADR-0001 Versioning).
- The audit hash chain grows with every entry and signature. Verification loads a full organization chain into memory today (`AuditEventIntegrity.md` §8); batched verification may become necessary.
- Audit appends serialize per organization (`AuditEventIntegrity.md` §5); journal writes share that serialization.
- How the first acknowledgement of the regulation is obtained before an employee can sign electronically is decided by P11-005.
- The legal sufficiency of the regulation is confirmed outside the platform before electronic journals replace paper.
- Enhanced or qualified electronic signatures require a future ADR.

---

# Related ADRs

- ADR-0001 Entity-Centric Architecture
- ADR-0002 Knowledge Object Specification
- ADR-0003 Metadata Engine
- ADR-0005 Obligations Engine
- ADR-0006 Document and Evidence Storage
- ADR-0007 Background Worker and Scheduling
- ADR-0008 HR Integration Contract
- ADR-0009 Knowledge Blocks and Document Assembly

---

# Decision Summary

Journals are append-only electronic registers; corrections are reversal entries.

Every entry and every signature record is committed to the existing audit hash chain by its SHA-256, and the verification script, extended by P11-005, detects modified, deleted, and inserted records.

Employees sign their own entries with a simple electronic signature from their own session; the signature is a separate append-only record, and the entry never changes.

Entry schemas are metadata, and printable forms are generated from the electronic register.
