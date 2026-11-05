# Document Shelf

Status: Phase 2 implemented (TASK-P11-012 §2; plan
`docs/superpowers/plans/2026-11-05-p11-012-phase-2-shelf-domain-api.md`). Import (phase 3),
frontend and signed scans (phase 4) and acknowledgement coverage (phase 5) follow.

## Place, document, requirement

- A **place** (`ShelfSlot`) is a slot the organization must fill: «what should be on the
  shelf». It has a code such as `ТрБ.02.02`, a short title for the spine, its legal basis,
  how binding it is, and a curated status. A place exists even when no document exists yet.
- A **document** (`ComplianceDocument`, TASK-P11-001) is an edition that fills a place.
  A place links its editions (`linked_document_ids`, in link order). At most one linked
  edition is in force (`active` or `under_review`).
- A **requirement** (`RegulatoryRequirement`, TASK-P11-009) will point at a place
  (many-to-one). The shelf does not depend on it.

Sections (`ShelfSection`, e.g. `ТрБ`) group places into shelves. Subsections (`ТрБ.02`) are
value objects of the section. Sections and subsections are only created or renamed, never
removed. The place code must start with its section code and name an existing subsection.

Persistence: migration `0015_document_shelf` with tables `shelf_sections`,
`shelf_subsections`, `shelf_slots` and `shelf_slot_documents`
(`docs/architecture/ComplianceDocumentPersistence.md` covers the documents).

## Effective status (backend-authoritative)

`ShelfStatusEvaluator.evaluate(slot, linked_documents, document_types, today)` is a pure
function. Handlers pass `today` = the UTC date of `ClockContract.now()`. The first matching
rule wins:

1. `excluded`: the place is excluded.
2. A linked document is in force. The current edition is the one with the latest
   `effective_from`, then the latest `updated_at`. Its status gives the place status:
   - `under_review` if that document is `under_review`;
   - `overdue_review` if the review date is before today;
   - `review_due` if the review date is at most N days from today. N is the largest of the
     type's `warning_thresholds_days`, or 90 when the type is unknown;
   - `present` otherwise, or when there is no review date.
3. A linked document is `draft` or `approved` only: `in_progress`.
4. Otherwise the curated status decides:

   | Curated status | Effective status |
   |---|---|
   | `present` | `present_unverified` (curated, no document in SafetyMAIN) |
   | `present_needs_review` | `review_due` |
   | `in_progress` | `in_progress` |
   | `missing` | `missing` |
   | `to_clarify` | `to_clarify` |

The review date is `next_review_at`. Without it, it is `effective_from` plus
`review_period_months` of the document type, and without that, of the place.

### Known divergence from P11-001 D11

The documents registry (`is_review_due`, D11) treats a document as due only when its
**type** has `review_period_months`. The shelf also falls back to the **place's**
`review_period_months`. So a place can show «Пересмотр» while the document page does not.
This is intentional for phase 2 (plan P9): aligning both would change P11-001 behaviour. A
later task may read one rule from a shared service.

### Groups and readiness

| Group | Effective statuses |
|---|---|
| «Есть» `present` | `present`, `present_unverified` |
| «Пересмотр» `review` | `review_due`, `overdue_review`, `under_review` |
| «В работе» `in_progress` | `in_progress` |
| «Нет» `missing` | `missing` |
| «Уточнить» `to_clarify` | `to_clarify` |
| «Исключено» `excluded` | `excluded` |

Readiness (D12) = `(present + excluded) / total`, as an integer percent rounded half up.
An empty shelf has 0. `mandatory_total` counts mandatory places, excluded ones included.

## Available actions

The evaluator also returns the actions for the current user. The router computes
`can_curate` (`shelf:curate`) and `can_create_document` (`compliance_document:create`)
without auditing a denial, because this check only shapes the response.

| Effective status | Primary | Other (curator) |
|---|---|---|
| `missing` | `develop_document` | `link_document`, `exclude` |
| `to_clarify` | `confirm_applicable` | `exclude` |
| `in_progress` | `open_project` | `link_document`, `exclude` |
| `present_unverified` | `upload_scan` | `link_document`, `exclude` |
| `present` | `open_document` (`send_for_acknowledgement` in phase 5) | `exclude` |
| `review_due`, `overdue_review` | `start_review` | `exclude` |
| `under_review` | `open_document` | `exclude` |
| `excluded` | `restore` | — |

Users without `shelf:curate` get only `open_document` or `open_project`, and only where a
target document exists.

Actions that act on a document are offered only when that document exists (plan P8a):

- `open_document` and `start_review` need a current in-force document;
- `open_project` needs a linked `draft` or `approved` document.

So a curated `present_needs_review` or `in_progress` place without documents has no
primary action. `develop_document` is hidden from a curator without
`compliance_document:create`.

## Exclusion

Curators exclude a place with a reason (`not_applicable`, `condition_not_met`, `duplicate`,
`other`) and a comment of 5–1000 characters after trimming. The place stays on the shelf as
excluded and keeps its code: codes are unique per organization, excluded places included.

- The curated status before exclusion is kept. **Restore** brings it back.
- Places imported as «Не применимо» are kept with status `to_clarify` before exclusion
  (phase 3).
- While excluded, a place allows only restore and detail edits, and its curated status is
  frozen.
- **Bulk exclusion** is all-or-nothing, with one audit event per place.

## Commands and transactions

Every command runs in one unit of work: load in the caller's organization (foreign → 404),
apply one domain transition, save with `UPDATE … WHERE version`, record
`compliance.place.*`, commit. Two kinds of no-op save nothing and record nothing: an edit
that changes nothing, and linking a document that is already linked.

**Develop** creates the draft with `build_compliance_document`, the same helper
`CreateComplianceDocumentHandler` uses (TASK-P11-001 A6). It adds the document and saves
the linked place in the same unit of work. The SQLAlchemy unit of work commits only once,
so the create handler's own `handle()` is not nested.

Unlinking deletes only the row in `shelf_slot_documents`. The unlink is audited; documents,
places and sections are never deleted.

## Audit

Resource types `SHELF_PLACE` and `SHELF_SECTION` (and `SHELF` for the import), subject
domain `SHELF`. The events are listed in `docs/architecture/AuditTaxonomy.md`.

## Import contract (phase 3)

The workbook import upserts sections, subsections and places by code. It fills
`import_fingerprint` and `last_imported_at`. It never overwrites fields edited in SafetyMAIN
since the previous import (D3) and emits `compliance.shelf.imported` once per run. Phase 2
reserves the fields and the audit descriptor; nothing sets them yet.
