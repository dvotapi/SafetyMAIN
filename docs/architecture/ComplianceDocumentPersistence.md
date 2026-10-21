# Compliance Document Persistence

Persistence layer for the TASK-P11-001 compliance documentation aggregate. See also
[ADR-0006](ADR-0006-Document-and-Evidence-Storage.md) (object storage) and
[docs/domain/ComplianceDocuments.md](../domain/ComplianceDocuments.md) (domain model).

## Tables (migration `0013_compliance_documents`)

- `document_types` — organization-scoped catalog (23 seeded entries per org).
  Columns: `id` (UUID PK), `organization_id` (UUID NOT NULL, FK), `code` (text),
  `title_ru` (text), `safety_domain`, `subject_kind`, `review_period_months`,
  `validity_months`, `periodicity_months`, `warning_thresholds_days` (int array),
  `requires_acknowledgement`, `requires_approval_order`, `legal_basis`,
  `legal_basis_reference`, `is_active`, timestamps.
  Unique: `(organization_id, code)`.
- `compliance_documents` — aggregate root.
  Columns include lifecycle fields (`status`, `status_before_archive`,
  `archive_reason`), scheduling (`issued_at`, `effective_from`, `next_review_at`),
  references (`approved_by_document_id`, `supersedes_document_id`,
  `superseded_by_document_id`), source enum, `applicability` (JSONB), optimistic
  concurrency `version`, timestamps and audit identities.
- `document_files` — ordered one-to-many child of `compliance_documents`, carrying each
  file's `bucket`, `key`, `size_bytes`, `content_type`, `sha256`, `original_filename`,
  `uploaded_at`, `uploaded_by`. Deletes cascade with the parent document.

### D9: unique code for in-force documents

A partial unique index enforces the invariant that no two in-force
(`active`/`under_review`) documents of the same organization share a code:

```sql
CREATE UNIQUE INDEX compliance_documents_code_in_force_unique
ON compliance_documents (organization_id, code)
WHERE status IN ('active', 'under_review');
```

Draft, approved, superseded and archived editions can keep the historical code
without conflicting with a current in-force document.

## SQLAlchemy mapping

- Models live in `backend/core/infrastructure/persistence/sqlalchemy/models/`
  (`document_type.py`, `compliance_document.py`, `document_file.py`).
- Mappers in `.../mappers/` translate rows to the frozen domain entities.
- Repositories in `.../repositories/` implement
  `DocumentTypeRepositoryContract` and `ComplianceDocumentRepositoryContract`.
  Both the SQLAlchemy and in-memory repositories enforce D9 by rejecting an
  `add`/`save` that would create a second in-force document with the same code
  (`DuplicateActiveComplianceDocumentCode`, 409).

## Unit of work

Both the SQLAlchemy and in-memory UoW expose `document_types` and
`compliance_documents`. Lifecycle handlers that touch two aggregates (e.g. activation
with supersession) call `save` on each one inside a single `begin → commit` cycle
through `run_audited_admin_operation`.

## Storage port

Files are addressed by `(bucket, key)` where the key follows D4:

```
<organization_id>/compliance_document/<document_id>/<upload_id>/<safe_filename>
```

Upload uses `StorageContract.create_upload_url` to issue a presigned PUT; the API
never proxies bytes. Confirmation calls `StorageContract.head` to verify size and
content type (and SHA-256 when the adapter returned it — D20 accepts a missing
value). Downloads call `StorageContract.create_download_url` with an attachment
`Content-Disposition` built per RFC 5987.

Production uses `S3Storage` (Yandex Object Storage); non-production without
`STORAGE_BUCKET` falls back to `InMemoryStorage`. Tests always use `InMemoryStorage`
via `container.storage`.
