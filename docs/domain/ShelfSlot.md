# ShelfSlot and ShelfSection domain

Bounded context: compliance documentation (TASK-P11-012 §2.1). Architecture, effective
status and actions: `docs/architecture/DocumentShelf.md`. API: `docs/api/ShelfAPI.md`.

## ShelfSection

Organization-owned catalogue entity: one shelf of the bookcase.

| Field | Rules |
|---|---|
| `code` | `^[А-ЯЁа-яё]{2,6}$`, unique per organization, immutable |
| `number` | 1–99, unique per organization, shelf order |
| `title` | non-empty |
| `safety_domain` | `SafetyDomain` |
| `subsections` | ordered `ShelfSubsection(id, code, title, position)`; `code` = `SECTION.SS` (two digits), unique within the section; `position` = append order |
| `version` | optimistic concurrency |

Methods: `create`, `rename`, `add_subsection`, `rename_subsection`. There is no removal.

## ShelfSlot (aggregate root)

| Field | Rules |
|---|---|
| `code` | `ShelfSlotCode`, `^[А-ЯЁа-яё]+\.\d{2}\.\d{2}$`. The prefix is the section code, `SECTION.SS` an existing subsection. Unique per organization, excluded places included. Immutable |
| `title` | 1–500 characters |
| `short_title` | 1–40 characters (spine label) |
| `document_kind` | one of `SHELF_DOCUMENT_KINDS` (17 values, `shelf_values.py`) |
| `kept_on` | `organization`, `facility`, `event`, `employee`, `asset`, `profession` |
| `obligation_level` | `mandatory`, `conditional` (requires `applicability_condition`), `recommended` |
| `legal_basis` | `SlotLegalBasis(regulation, clause, quote, source_url, confidence)` |
| `review_cycle_text`, `review_period_months` (≥ 1 or null) | |
| `curated_status` | `present`, `present_needs_review`, `in_progress`, `missing`, `to_clarify` |
| `document_type_code` | must exist and be active in the catalog when set (checked by the handlers) |
| `proposed_document_type`, `responsible_text`, `legacy_location`, `notes`, `package_code`, `legacy_code` | free text carried from the workbook |
| `exclusion` | `SlotExclusion(reason, comment, status_before, excluded_by, excluded_at)` or null |
| `linked_document_ids` | ordered, distinct |
| `import_fingerprint`, `last_imported_at` | set by the phase 3 import only |
| `created_*`, `updated_*`, `version` | |

## Transitions

| Method | Precondition | Effect |
|---|---|---|
| `create` | code matches the section and an existing subsection | version 1 |
| `update_details` | curated fields only; on an excluded place the curated status cannot change | returns the same place when nothing changes |
| `exclude` | not excluded; comment ≥ 5 characters after trimming | stores `status_before` |
| `restore` | excluded | `curated_status = status_before` |
| `confirm_applicable` | not excluded, curated status `to_clarify` | curated status `missing` |
| `link_document` | not excluded, same organization, `subject_kind = organization`; at most one linked document in force | idempotent |
| `unlink_document` | not excluded; the document is linked | removes the link only |
| `ensure_can_develop` | not excluded; no linked document `draft`, `approved`, `active`, `under_review` | — |

Each transition checks `expected_version` and raises a domain exception from
`backend/core/domain/exceptions/shelf.py` on a violation.

The shelf has no domain event classes (plan P4). The audit log (`compliance.place.*`,
`compliance.section.*`) records every change, as for `ComplianceDocument`.
