# Compliance Documents API

Organization-scoped REST surface for the ComplianceDocument aggregate (TASK-P11-001).
All endpoints live under `/api/v1/compliance-documents` and require bearer authentication
plus the `X-Organization-Id` header. Cross-tenant access is masked as `404 compliance_document_not_found` — never `403` and never a payload leak.

Lifecycle (D1–D20):

```
draft --(approve)--> approved --(activate)--> active
                                               |
                                               +-- (start-review) --> under_review
                                               |                        |
                                               |                        +-- (complete-review) --> active
                                               |                        |
                                               |                        +-- (supersede*) --> superseded
                                               +-- (supersede*) ------> superseded
                                               +-- (archive)      ----> archived
archived --(restore)--> previous status (D8)
```

`supersede` is not an explicit action: activating a new edition whose
`supersedes_document_id` points to an in-force (`active`/`under_review`) edition of the
same type atomically transitions the old one to `superseded` and writes a reverse
`superseded_by_document_id` link (D16).

## Permissions

| Action | Permission | Roles that hold it |
|---|---|---|
| List / get / list file versions / get download URL | `compliance_document:read` | admin, member, auditor |
| Create / update | `compliance_document:create` / `compliance_document:update` | admin, member |
| Upload URL / confirm file | `compliance_document:update` | admin, member |
| Approve | `compliance_document:approve` | admin |
| Activate / complete-review | `compliance_document:activate` | admin |
| Start-review | `compliance_document:update` (D10) | admin, member |
| Archive / restore | `compliance_document:archive` (D10) | admin |

## CRUD (Phase 4)

### `POST /compliance-documents` — `create_compliance_document`

Creates a draft. Request body matches `CreateComplianceDocumentRequest`. Returns `201`
with a `Location` header to the new document. Soft existence check on
`approved_by_document_id` / `supersedes_document_id` (full type/status check runs on
activate).

### `GET /compliance-documents` — `list_compliance_documents`

Query parameters: `document_type_id` (repeatable UUID), `status`, `subject_kind`,
`safety_domain`, `review_due`, `include_archived`, `search`, `offset`, `limit`.
`is_review_due` is computed backend-side using the configured clock (D11/D14/D15).

### `GET /compliance-documents/{document_id}` — `get_compliance_document`

Returns one document with `is_review_due` resolved. 404 when the document is in another
organization or does not exist.

### `PATCH /compliance-documents/{document_id}` — `update_compliance_document`

Partial update of a draft. `null` on a nullable field clears it; omitting the key leaves
it untouched. 422 `compliance_document_cannot_be_modified` when the document is not
`draft`. 409 `compliance_document_version_conflict` when `expected_version` is stale.

## Lifecycle (Phase 5)

All lifecycle actions take `{ "expected_version": <int>, ... }`. Response is the updated
`ComplianceDocumentResponse`.

| Method & path | Operation ID | Request body (extra fields) | Audit action |
|---|---|---|---|
| `POST .../{id}/approve` | `approve_compliance_document` | — | `compliance.document.approved` |
| `POST .../{id}/activate` | `activate_compliance_document` | — | `compliance.document.activated` (+ `compliance.document.superseded` for the previous edition when applicable) |
| `POST .../{id}/start-review` | `start_review_compliance_document` | — | `compliance.document.review_started` |
| `POST .../{id}/complete-review` | `complete_review_compliance_document` | `completed_on` (date), optional `next_review_at` (date) | `compliance.document.review_completed` |
| `POST .../{id}/archive` | `archive_compliance_document` | `reason` (non-empty) | `compliance.document.archived` |
| `POST .../{id}/restore` | `restore_compliance_document` | `reason` (non-empty) | `compliance.document.restored` |

Activation preconditions:

- A current file must be attached (`compliance_document_validation_error` otherwise).
- `effective_from` must be set.
- When the document's type has `requires_approval_order=true`:
  - `approved_by_document_id` must be set.
  - It must point to a same-organization document whose type code is `order` and whose
    status is `active` or `under_review`.
- When `supersedes_document_id` is set, the referenced document must exist in the same
  organization, be the same type, and currently be `active` or `under_review`.

Both the activated document and the superseded previous edition are persisted in the
same unit of work (atomic).

### Common error envelopes

| HTTP | Code | When |
|---|---|---|
| 404 | `compliance_document_not_found` | Unknown id or cross-tenant |
| 409 | `compliance_document_version_conflict` | Stale `expected_version` |
| 409 | `duplicate_compliance_document_code` | Another in-force document owns the code (D9) |
| 422 | `invalid_compliance_document_transition` | Illegal source → target |
| 422 | `compliance_document_cannot_be_modified` | Write on non-draft |
| 422 | `compliance_document_validation_error` | Missing file/effective_from, bad approving order, missing supersede target, applicability errors |
| 422 | `compliance_document_reason_required` | Archive/restore without a reason |

## File subresource (ADR-0006)

Files only attach in `draft` (D6). A new edition that needs a different file is a new
document, chained via `supersedes_document_id` on activation.

### `POST .../{id}/files/upload-url` — `create_compliance_document_upload_url`

Permission: `compliance_document:update`.

Request:

```json
{
  "filename": "briefing.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2048,
  "sha256": "<64 hex chars>"
}
```

Validation:

- `content_type` must be in the allow-list: `application/pdf`,
  `application/vnd.openxmlformats-officedocument.wordprocessingml.document`,
  `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`,
  `image/png`, `image/jpeg`
  (`compliance_document_file_type_not_allowed`).
- `size_bytes <= STORAGE_MAX_UPLOAD_BYTES` (`compliance_document_file_too_large`).
- `sha256` must be 64 lowercase hex characters.
- Document must be `draft` (`compliance_document_validation_error`).

Response:

```json
{
  "upload_id": "<uuid>",
  "bucket": "...",
  "key": "<org>/compliance_document/<document_id>/<upload_id>/<safe_filename>",
  "url": "<presigned PUT url>",
  "method": "PUT",
  "headers": { "Content-Type": "application/pdf", "x-amz-meta-sha256": "..." },
  "expires_at": "<iso datetime>"
}
```

The client PUTs the bytes directly to the signed URL, sending the listed headers
verbatim and a body of exactly `size_bytes`. No file bytes ever pass through the API.

### `POST .../{id}/files/confirm` — `confirm_compliance_document_file`

Permission: `compliance_document:update`.

Request:

```json
{
  "expected_version": 1,
  "bucket": "...",
  "key": "...",
  "size_bytes": 2048,
  "sha256": "<64 hex>",
  "content_type": "application/pdf",
  "original_filename": "briefing.pdf"
}
```

Validation (`compliance_document_validation_error` for any mismatch):

- `key` must start with `<org>/compliance_document/<document_id>/`.
- `storage.head(bucket, key)` must find the object.
- `size_bytes` and `content_type` must match the stored object.
- `sha256` is compared when storage returned it; a missing SHA from storage is an
  accepted risk (D20) and does not fail confirmation.

On success the file is attached as the current file and the document's `version` bumps.
Audit: `compliance.document.file_attached` (legacy identifier per D5).

### `GET .../{id}/files/current/download-url` — `get_compliance_document_download_url`

Permission: `compliance_document:read`. Response:

```json
{
  "url": "<presigned GET url>",
  "expires_at": "<iso datetime>",
  "filename": "briefing.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2048,
  "sha256": "..."
}
```

The signed URL forces `Content-Disposition: attachment` with an RFC 5987 UTF-8 filename
and the stored `Content-Type`. 404 `compliance_document_file_not_found` when the
document has no attached file. 404 `compliance_document_not_found` for cross-tenant.

### `GET .../{id}/files/versions` — `list_compliance_document_file_versions`

Permission: `compliance_document:read`. Returns every file ever attached, oldest first.
Phase 5 only writes files on `draft`, so most documents have one entry; the endpoint is
in place for future supersession-with-reupload workflows.
