# Document Shelf API

Organization-scoped REST surface of the document shelf («Полка», TASK-P11-012 §2.5).
All endpoints live under `/api/v1/shelf` and need bearer authentication plus the
`X-Organization-Id` header. A place, section or document of another organization is
answered with `404`, never `403`, and never leaks a payload.

The backend is authoritative: effective status, status group, review date, readiness,
counts and `available_actions` are computed by `ShelfStatusEvaluator`
(`backend/core/application/services/shelf_status_evaluator.py`). Clients display them
and must not recompute them. Rules: `docs/architecture/DocumentShelf.md`.

There are no DELETE endpoints. Places, sections and documents are never removed;
unlinking a document is an audited POST command.

## Permissions

| Action | Permission | Roles |
|---|---|---|
| Overview, one shelf, search, place detail | `shelf:read` | admin, member, auditor |
| Create / edit / exclude / restore / bulk-exclude / confirm-applicable / unlink | `shelf:curate` | admin (P11-009 adds `compliance_curator`) |
| Link a document | `shelf:curate` + `compliance_document:read` | admin |
| Develop a document | `shelf:curate` + `compliance_document:create` | admin |

Denials of both shelf permissions are audited as `authorization.permission_denied`
with resource type `SHELF_PLACE`.

## Endpoints

| Method | Path | Success |
|---|---|---|
| GET | `/shelf` | 200 `ShelfOverviewDto` |
| GET | `/shelf/sections/{section_code}/slots` | 200 `ShelfSectionSlotsDto`; unknown section → 404 `shelf_section_not_found` |
| GET | `/shelf/slots?q=&limit=50` | 200 `{items: ShelfSlotSummaryDto[]}` |
| GET | `/shelf/slots/{slot_id}` | 200 `ShelfSlotDetailDto` |
| POST | `/shelf/slots` | 201 `ShelfSlotDetailDto` + `Location` |
| PATCH | `/shelf/slots/{slot_id}` | 200 `ShelfSlotDetailDto` |
| POST | `/shelf/slots/{slot_id}/exclude` | 200 `ShelfSlotDetailDto` |
| POST | `/shelf/slots/{slot_id}/restore` | 200 `ShelfSlotDetailDto` |
| POST | `/shelf/slots/bulk-exclude` | 200 `{items: ShelfSlotSummaryDto[]}` |
| POST | `/shelf/slots/{slot_id}/confirm-applicable` | 200 `ShelfSlotDetailDto` |
| POST | `/shelf/slots/{slot_id}/documents` | 200 `ShelfSlotDetailDto` |
| POST | `/shelf/slots/{slot_id}/documents/{document_id}/unlink` | 200 `ShelfSlotDetailDto` |
| POST | `/shelf/slots/{slot_id}/develop` | 201 `{document_id, slot: ShelfSlotDetailDto}` + `Location` of the document |

`section_code` is Cyrillic (`ТрБ`, `ПожБ`) and is sent URL-encoded. Request bodies reject
unknown fields. Every command takes the place's current `version` (optimistic
concurrency).

`import_fingerprint` and `last_imported_at` are set only by the workbook import
(`docs/guides/ShelfImport.md`) and are not part of the API.

Sections and subsections have no endpoints yet. They are created by the phase 3 workbook
import through the application handlers `CreateShelfSection`, `RenameShelfSection`,
`AddShelfSubsection` and `RenameShelfSubsection`.

## DTOs

`ShelfOverviewDto`

```json
{
  "sections": [ShelfSectionSummaryDto],
  "totals": {"places": 416, "excluded": 3, "by_group": GroupCounts, "readiness_percent": 41},
  "evaluated_at": "2026-11-05T09:00:00Z",
  "last_imported_at": "2026-11-05T08:00:00Z"
}
```

`GroupCounts` = `{present, review, in_progress, missing, to_clarify, excluded}`.
`last_imported_at` is the latest workbook import of the organization's places, or `null`
before the first one.

`ShelfSectionSummaryDto`: `code, number, title, safety_domain, total, mandatory_total,
by_group, readiness_percent, strip[{code, group}]`. Sections are ordered by `number`.
Places in `strip` are in code order. `mandatory_total` counts excluded places too.

`ShelfSlotSummaryDto`: `id, code, subsection_code, short_title, title, document_kind,
kept_on, obligation_level, effective_status, group, has_acknowledgement_gap`.
`has_acknowledgement_gap` is always `false` until phase 5.

`ShelfSectionSlotsDto`: `section {code, number, title}`,
`subsections[] {code, title, slots[ShelfSlotSummaryDto]}`. Subsections and places are in
code order.

`ShelfSlotDetailDto` = summary fields plus:

| Field | Notes |
|---|---|
| `section_code` | |
| `legal_basis` | `{regulation, clause, quote, source_url, confidence}` |
| `applicability_condition`, `review_cycle_text`, `review_period_months` | curated |
| `review_date` | from the evaluator; `null` without a current in-force document |
| `curated_status` | `present`, `present_needs_review`, `in_progress`, `missing`, `to_clarify` |
| `document_type_code`, `proposed_document_type`, `responsible_text`, `legacy_location`, `notes`, `package_code`, `legacy_code` | curated |
| `exclusion` | `{reason, comment, excluded_by_name, excluded_at}` or `null`. `excluded_by_name` is `""` when the user no longer exists |
| `current_document` | `{id, code, title, status, effective_from, next_review_at, approved_by_order{code, title}\|null, signed_scan, working_file{file_id, content_type, size_bytes, uploaded_at}\|null}` or `null`. `signed_scan` is the current signed scan and `working_file` the current working file. Both carry `file_id`, so the viewer gets an inline URL from `GET /compliance-documents/{id}/files/{file_id}/view-url` |
| `editions[]` | `{id, code, status, effective_from}` of every linked document; newest `effective_from` first, unset last |
| `available_actions[]` | every action offered to the current user, `primary_action` first |
| `primary_action` | action or `null` |
| `acknowledgement` | always `null` until phase 5 |
| `version` | |

Actions: `develop_document`, `link_document`, `exclude`, `restore`, `confirm_applicable`,
`open_project`, `open_document`, `upload_scan`, `upload_signed_scan`, `start_review`,
`send_for_acknowledgement`. `upload_signed_scan` is offered to curators who hold
`compliance_document:update` while the current in-force document has no signed scan. It
is placed before `exclude`.

## Requests

| Request | Body |
|---|---|
| Create | `{code, title, short_title, document_kind, kept_on, obligation_level, curated_status="missing", applicability_condition, legal_basis, review_cycle_text, review_period_months, document_type_code, proposed_document_type, responsible_text, legacy_location, notes, package_code, legacy_code}` |
| Edit | `{version, …any curated field}`. Only the fields present change. `null` clears `review_period_months` or `document_type_code`; `null` for `legal_basis` resets it to empty. `code` and exclusion cannot be edited |
| Exclude | `{reason, comment, version}`; reasons `not_applicable`, `condition_not_met`, `duplicate`, `other`; comment 5–1000 characters after trimming |
| Restore, confirm-applicable, unlink | `{version}` |
| Bulk exclude | `{items: [{slot_id, version}] (1–200, distinct), reason, comment}` |
| Link | `{document_id, version}` |
| Develop | `{document_type_code?, version}` |

`legal_basis.source_url` must be an absolute `http` or `https` URL of at most 2048
characters (it is shown as a link); blank means none.

Search: `q` is 1–100 characters and is a case-insensitive substring of `code`, `title` or
`short_title`. `limit` defaults to 50, at most 100. Results are in code order and include
excluded places.

## Command semantics

- **Exclude** stores the curated status before exclusion; **restore** brings it back.
  An excluded place allows only restore and detail edits (its curated status stays
  frozen). Any other command returns `already_excluded`.
- **Confirm applicable** works only from `to_clarify`; the place becomes `missing`.
- **Link** needs a document of the same organization (else 404
  `compliance_document_not_found`) with `subject_kind = organization` (else
  `document_subject_not_supported`). Linking an already linked document is a no-op:
  no version change, no audit event. A second linked document in force (`active`,
  `under_review`) is rejected with `already_linked_active_document`.
- **Unlink** removes only the link. The document stays. A document that is not linked → 404
  `shelf_slot_document_not_linked`.
- **Bulk exclude** is all-or-nothing in one unit of work. Every place is loaded and
  checked before any change:
  - any unknown or foreign id → 404 for the whole request;
  - any version mismatch → 409 with `details.conflicting_slot_ids`;
  - any place already excluded → 422 `already_excluded` with `details.excluded_slot_ids`.

  Each excluded place gets its own audit event.
- **Develop** creates a `draft` ComplianceDocument with `code` = place code, `title` =
  place title, source `manual`. The type is the request `document_type_code` or else the
  place's. It links the document in the same unit of work and records
  `compliance.document.created` and `compliance.place.linked`. It is rejected when:
  - a linked document is `draft`, `approved`, `active` or `under_review` →
    `already_linked_active_document`;
  - neither the request nor the place names a type → `document_type_required`;
  - the type is unknown or inactive → `document_type_not_found` (422).

  The document is built by the same code path as `POST /compliance-documents`
  (`build_compliance_document`).

## Errors

| Status | Code | When |
|---|---|---|
| 401 | `unauthenticated` | no or invalid bearer token |
| 403 | `permission_denied` | missing `shelf:*` or the extra document permission |
| 404 | `shelf_slot_not_found`, `shelf_section_not_found`, `compliance_document_not_found`, `shelf_slot_document_not_linked` | unknown or other organization |
| 409 | `duplicate_shelf_slot_code` | code already used in the organization, excluded places included |
| 409 | `shelf_slot_version_conflict` | stale `version` (bulk: `details.conflicting_slot_ids`) |
| 422 | `shelf_slot_code_mismatch` | the code names no existing section or subsection |
| 422 | `shelf_slot_validation_error` | invalid field (code format, lengths, `document_kind` outside the vocabulary, conditional place without a condition, repeated bulk items) |
| 422 | `document_type_not_found` | `document_type_code` not in the active catalog |
| 422 | `comment_too_short`, `already_excluded`, `not_excluded`, `not_to_clarify`, `document_subject_not_supported`, `document_type_required`, `already_linked_active_document` | preconditions of §2.5 |
| 422 | `request_validation_error` | body or query shape |

## Audit

Every command records `compliance.place.*` with resource type `SHELF_PLACE`:
`created`, `updated`, `excluded`, `restored`, `confirmed`, `linked`, `unlinked`.
Metadata: `slot_id`, `slot_code`, `section_code`, `previous_status`, `new_status`,
`expected_version`, `resulting_version`. Some events add more:

- `updated`: `changed_fields`;
- `excluded`: `reason` and `comment`;
- `linked`, `unlinked`: `document_id` and `document_code`.

Known failures (conflicts, preconditions) are recorded with outcome `FAILURE`. Details:
`docs/architecture/AuditTaxonomy.md`.
