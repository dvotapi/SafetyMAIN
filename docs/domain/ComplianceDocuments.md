# ComplianceDocument domain

TASK-P11-001 introduces two organization-scoped aggregates: `DocumentType` (catalog)
and `ComplianceDocument` (document instance). This note captures the invariants and
lifecycle. The API surface lives in
[docs/api/ComplianceDocumentsAPI.md](../api/ComplianceDocumentsAPI.md); persistence in
[ComplianceDocumentPersistence](../architecture/ComplianceDocumentPersistence.md).

## DocumentType

Organization-scoped catalog entry describing a kind of compliance document.

Invariants:

- Exactly one of `review_period_months`, `validity_months`, `periodicity_months` may
  be set.
- `warning_thresholds_days` is a non-empty tuple of positive integers.
- `requires_approval_order=true` means instances must point to an in-force document of
  type `order` on activation.
- `is_active` controls whether new documents of this type can be created.

Current catalog is seeded (23 entries) via `scripts/seed_document_types.py` (D2):
`iot_profession`, `iot_work_type`, `production_instruction`, `regulation_suot`,
`order`, `briefing_program`, `induction_briefing`, `workplace_briefing`,
`fire_briefing`, `electrical_group`, `height_permit`, `confined_space_permit`,
`hot_work_permit`, `driver_permit`, `pre_trip_inspection`, `medical_check`,
`training_certificate`, `training_journal`, `incident_journal`,
`emergency_contact_list`, `evacuation_plan`, `osago`, `vehicle_inspection`.

## ComplianceDocument

### State

| Field | Role |
|---|---|
| `document_type_id` | Type (same org). |
| `subject_kind` + `subject_id` | ORGANIZATION / EMPLOYEE / ASSET; the latter two carry a UUID. |
| `code`, `title` | Identity. `code` is unique among in-force documents (D9). |
| `status` | `draft` → `approved` → `active` ↔ `under_review`, exits to `superseded` or `archived`. |
| `issued_at`, `effective_from`, `next_review_at` | Scheduling. |
| `approved_by_document_id` | Order document authorising activation. |
| `supersedes_document_id` | Predecessor edition. |
| `superseded_by_document_id` | Reverse link (D16), set when a successor activates. |
| `applicability` | Positions / work types / departments / asset ids. |
| `source` | `manual` / `generated` / `hr_form`. |
| `files` | Ordered uploads; `current_file` is the newest. |
| `notes` | Free text. |
| `status_before_archive`, `archive_reason` | Set only in `archived`. |
| `created_at/by`, `updated_at/by`, `version` | Audit + optimistic concurrency. |

### Lifecycle (confirmed)

```
draft --(approve, requires file)--> approved
      --(archive)-------------------> archived
approved --(activate, requires file+effective_from, approval order if required,
             supersedes atomically)-> active
         --(archive)------------------> archived
active --(start_review)--> under_review
       --(archive)---------> archived
       --(supersede*)------> superseded
under_review --(complete_review, recomputes next_review_at from completed_on, D7)--> active
             --(supersede*)-----------------------------------------------------> superseded
superseded --(archive)--> archived
archived --(restore, back to status_before_archive, D8)--> previous
```

`*` supersession is not reachable from the UI directly — it is a side effect of
activating a new edition whose `supersedes_document_id` points at the old one.
Entity method `ComplianceDocument.supersede(replacement=...)` enforces that the
replacement is in the same organization, has the same `document_type_id`, is
`active`, and names this document as its predecessor; it stamps the reverse link.

### Invariants

- `subject_id` is required when `subject_kind != ORGANIZATION` and forbidden otherwise.
- Self-reference is rejected on `approved_by_document_id`, `supersedes_document_id`
  and `superseded_by_document_id`.
- Writes other than lifecycle transitions require `status=draft` (D6).
- Archive requires a non-empty reason; restore requires the same (D8).
- `is_review_due` is a backend-computed read-model flag (D11/D14/D15):
  returns true when the status is in force, `next_review_at` is set, the type has a
  review period, and `next_review_at <= today + max(warning_thresholds_days)`.
- Optimistic concurrency: every mutator takes `expected_version` and raises
  `ComplianceDocumentVersionConflict` on a stale write.

### DocumentFile value object

Carries `(bucket, key, size_bytes, content_type, sha256, original_filename,
uploaded_at, uploaded_by)` for one upload. SHA-256 is validated as 64 hex chars.
Files only attach while `status=draft`; the API refuses to issue an upload URL or
confirm a file otherwise.

## Decisions referenced

See `docs/tasks/TASK-P11-001-storage-and-compliance-documents.md` for the full D1–D20
decision log. Key ones for this domain:

- **D4** key scheme `<org>/compliance_document/<document_id>/<upload_id>/<safe>`.
- **D6** files only in draft.
- **D7** `complete_review` recomputes `next_review_at` from `completed_on`.
- **D8** restore returns to `status_before_archive`.
- **D9** partial unique index on in-force code.
- **D11/D14/D15** backend-computed `is_review_due`.
- **D16** reverse `superseded_by_document_id` link.
- **D17** `under_review → superseded` is allowed.
- **D18** `next_review_at` filled from the type on activation if not provided.
- **D19** `complete_review` works even on types without a review period.
- **D20** SHA-256 is client-asserted; a missing value from storage is accepted risk.
