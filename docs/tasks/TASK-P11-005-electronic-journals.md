# TASK-P11-005 — Electronic Journals with Simple Electronic Signature

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-004 (employees and accounts), TASK-P11-001 (documents), TASK-P11-003 (printable form templates; the e-signature regulation)

---

## Goal

Replace paper safety journals with append-only electronic registers whose
entries are signed by employees with a simple electronic signature (ПЭП),
are tamper-evident through the existing audit hash chain, and can be printed
in the regulated form when an inspector asks for paper.

Journals in scope for the first release: workplace briefing log (initial,
repeated, unscheduled, targeted), induction briefing log, fire-safety
briefing log, PPE issue log, knowledge-check log, equipment inspection log,
production-control log. All are one mechanism with different field schemas.

---

## Context

- ADR-0010 (P11-000) fixes append-only semantics, reversal entries, hash
  chaining, and the ПЭП record content.
- `docs/architecture/AuditEventIntegrity.md` and
  `scripts/verify_audit_integrity.py` — reuse the chain; do not build a
  second one.
- The domain already has `Training` (`training_permit_emergency_asset.py`)
  with statuses planned → in_progress → completed → expired; it has no
  persistence or API. This task persists it as the "event" behind briefing
  and knowledge-check entries.
- Employees and the `employee` role exist after P11-004. Corporate email is
  the identity; ПЭП confirmation happens in the employee's authenticated
  session.
- Regulated printable forms are DOCX templates (P11-003 template engine).

---

## Scope

### 1. Journal types (metadata)

`journal_types`: id, org, `code` (`briefing_workplace`, `briefing_induction`,
`briefing_fire`, `ppe_issue`, `knowledge_check`, `equipment_inspection`,
`production_control`), `title_ru`, `safety_domain`, `entry_schema` (JSON
Schema of entry fields: e.g. briefing kind enum, instructions[] as
`ComplianceDocument` refs, instructor employee ref, signature requirements),
`requires_employee_signature`, `requires_instructor_signature`,
`printable_template_id`, `legal_basis`, `retention_years`.

Seed all seven with schemas derived from the regulated forms.

### 2. Journals and entries

- `journals`: id, org, `journal_type_id`, `title`, `department`, `responsible_employee_id`,
  `opened_at`, `closed_at`, `status` (`active | closed | archived`), version.
- `journal_entries`: id, journal_id, `seq_no` (gap-free per journal, assigned
  in the unit of work), `kind` (`record | reversal`), `reverses_entry_id`,
  `occurred_at`, `payload` (validated against `entry_schema`),
  `subject_employee_ids[]`, `related_document_ids[]`, `training_id`
  (nullable), `author_user_id`, `created_at`, `status`
  (`awaiting_signature | signed | reversed`), `chain_hash`, `prev_chain_hash`.
- `journal_entry_signatures`: entry_id, `signer_employee_id`, `signer_user_id`,
  `role` (`subject | instructor | responsible`), `signed_at`, `client_ip`,
  `user_agent`, `payload_sha256`, `method` (`session_confirm` now;
  `email_code` reserved).
- Invariants: entries are immutable after creation (repository has no
  update method for payload); a reversal requires a reason and references an
  existing signed entry; `seq_no` is strictly increasing; `chain_hash =
  sha256(prev_chain_hash || canonical_json(entry))` and every entry is also
  emitted as an audit event so `verify_audit_integrity.py` covers journals.

### 3. Simple electronic signature

- Entry creation by an instructor/responsible creates signature requests for
  each subject employee (and the instructor, if required by the type).
- Employee signs from `/me/signatures` in their own session:
  `POST /api/v1/journal-entries/{id}/sign` — requires the caller's user to be
  linked to the subject employee; records the signature fields; when all
  required signatures are present the entry becomes `signed`.
- Signing shows the employee the entry content and the referenced
  instruction titles before confirming (the confirmation text is part of the
  e-signature regulation).
- Pending signatures older than N days (setting) are surfaced to the
  responsible person (P11-007 will email; here — UI counter only).

### 4. Training persistence

- Persist `Training` with a repository and migration; a briefing or
  knowledge-check entry creates a `Training` per subject employee with
  `completed_at = occurred_at` and `expires_at = occurred_at +
  periodicity_months` from the linked `DocumentType`
  (`ot_briefing_repeat` etc., seeded in P11-001).
- `Training` is the evidence object P11-006 consumes to close and reschedule
  briefing obligations.

### 5. Printable forms

- Worker job `render_journal` (period, journal) → DOCX/PDF from the type's
  printable template with entries in regulated column layout and signature
  cells showing "подписано ПЭП, дата, хэш" — uploaded to storage, offered for
  download; never replaces the electronic record.

### 6. API

```text
GET  /api/v1/journal-types
GET/POST /api/v1/journals ; GET/PATCH /api/v1/journals/{id} ; close | archive
GET  /api/v1/journals/{id}/entries    (pagination by seq_no, filters)
POST /api/v1/journals/{id}/entries    (validates payload against schema)
GET  /api/v1/journal-entries/{id}
POST /api/v1/journal-entries/{id}/reverse   (reason)
POST /api/v1/journal-entries/{id}/sign
GET  /api/v1/me/signatures            (employee role; pending + signed)
POST /api/v1/journals/{id}/render     (enqueue printable) ; GET render status/url
GET  /api/v1/trainings                (filters: employee, type, expiring)
```

Permissions: `journal:read | create | manage`, `journal_entry:create |
reverse`, `journal_entry:sign_self` (employee), `training:read`.
Audit: `compliance.journal.*`, `compliance.journal_entry.created |
signed | reversed`, `safety.training.completed`.

### 7. Frontend

- Journals registry and journal page: entries feed (newest first), schema
  driven entry form (generated from `entry_schema` via a shared JSON-Schema
  form renderer — put it in `components/forms/` if generic), signature
  status chips, reversal dialog, "Печатная форма" action.
- Employee `/me/signatures`: pending list with entry content and one-click
  confirm; history.
- Employee object page "Журналы" tab (P11-004 placeholder).

### 8. Documentation

`docs/architecture/ElectronicJournals.md` (chain, signatures, legal notes),
`docs/api/JournalsAPI.md`, `docs/domain/Training.md`, runbook section on
verifying journal integrity, `CLAUDE.md`.

---

## Acceptance Criteria

- Creating a briefing entry for three employees produces three signature
  requests; each employee can sign only their own; the entry becomes
  `signed` after all required signatures; `Training` rows exist with correct
  `expires_at`.
- Payload update is impossible at repository and API level (tests); a
  reversal creates a new entry and leaves the original readable with
  `reversed` status.
- `scripts/verify_audit_integrity.py` detects a manually modified
  `journal_entries.payload` row.
- Printable DOCX/PDF for a period renders with signatures marked as ПЭП.
- Schema-driven entry form renders all seven seeded types without
  type-specific code; `npm run verify` passes; E2E covers create entry →
  employee signs.

---

## Non-Goals

- Enhanced/qualified signatures, SMS codes.
- Automatic creation of entries from training providers.
- Obligation scheduling and reminders (P11-006/007).
- Migration of historical paper journals (may be entered manually with
  `occurred_at` in the past — allowed, audited).

---

## Verification

Domain/application tests for invariants and hashing; `db` tests for
`seq_no` concurrency (two parallel inserts); security matrix for
`sign_self`; frontend tests; integrity script run in CI against a seeded
journal.

---

## Suggested implementation phases

1. Journal types + schemas + seeds; Training persistence.
2. Journals/entries/signatures domain + repos + migration + chain.
3. API + RBAC + audit + integrity script extension.
4. Printable rendering job.
5. Frontend (journals, entry form renderer, employee signing).
