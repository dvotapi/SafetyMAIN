# TASK-P11-001 — Object Storage and Organisational Compliance Documents

Status: In Progress (implementation plan approved 2026-10-01)
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-000 (ADR-0006, ADR-0009 sections on document types)

---

## Goal

Give SafetyMAIN the ability to store, version, approve, and review the
organisation's local normative acts — instructions (ИОТ, производственные
инструкции), regulations (положения), orders (приказы), briefing programs,
emergency plans (ПЛА) — with their files kept in object storage. This is the
first production vertical slice of the P11 epic and the foundation every
later task builds on.

After this task a safety specialist can upload the existing PDF instructions,
fill in their attributes, see the registry of local acts by safety domain,
and be told which documents are due for planned review.

---

## Context

- Nearest completed vertical slices: Hazard (`docs/tasks/TASK-P8-002.md`,
  `backend/api/routers/hazards.py`, `alembic/versions/0010_safety_hazards.py`)
  and Risk Control (`TASK-P9-007*`). Reuse their layering, RBAC, audit, and
  test structure.
- `KnowledgeObject` / `KnowledgeObjectRelation` exist and are the generic
  graph. Concrete aggregates (Hazard, RiskControl) are separate tables with
  their own repositories; follow that pattern (typed aggregate + relations
  for cross-links), do not stuff documents into the generic payload.
- Alembic head is `0012_risk_controls`. New migrations continue from `0013`.
- Permissions: `backend/core/domain/value_objects/permission.py`; roles
  `admin | member | auditor` in `role.py`; mapping in `role_permissions.py`.
- Audit families: `backend/core/domain/security_events/families/safety.py`
  (`safety.risk_control.*`). Add a `compliance` family.
- `backend/core/infrastructure/storage/` is empty; ADR-0006 defines the port.
- Frontend: Registry pattern (`docs/design/RegistryPattern.md`), Object Page,
  Russian copy (`docs/design/RussianUICopy.md`). `frontend/src/app/knowledge`
  is a placeholder route and is the natural home for "Локальные акты".
- The hr_form OCR schema (`hr_form/docs/medical/intake-ocr-schema.v1.json`)
  is the reference vocabulary for **employee** document types, which are
  seeded here but used by P11-008.

---

## Scope

### 1. Storage port and adapter

- `backend/core/contracts/storage.py`: `StorageContract` with
  `create_upload_url(key, content_type, max_bytes) -> PresignedUpload`,
  `create_download_url(bucket, key, ttl) -> str`, `head(bucket, key) -> ObjectInfo | None`.
- `backend/core/infrastructure/storage/s3_storage.py`: boto3 implementation;
  `in_memory_storage.py` for tests.
- Settings: `STORAGE_ENDPOINT_URL`, `STORAGE_REGION`, `STORAGE_BUCKET`,
  `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY`, `STORAGE_PRESIGN_TTL_SECONDS`,
  plus read-only credentials for external buckets
  `STORAGE_EXTERNAL_ACCESS_KEY` / `_SECRET_KEY` (used by P11-008).
  Production validation (`security_validation.py`) must reject an empty
  bucket or keys when `APP_ENV=production`.
- `docker-compose.yml`: add `minio` (+ bucket bootstrap) for development.
- Architecture test: `domain` and `application` must not import `boto3`.

### 2. `DocumentType` catalog (metadata)

Table `document_types` (organisation-scoped, with a system seed):

- `code` (unique per org, e.g. `iot_profession`, `iot_work_type`,
  `production_instruction`, `regulation_suot`, `order`, `briefing_program`,
  `emergency_plan`, `production_control_regulation`, and employee types
  `dopog_cert`, `driver_license`, `ekv`, `rtn_protocol`,
  `attestation_protocol`, `tractor_license`, `drilling_license`,
  `excavator_license`, `medical_conclusion`, `psychiatric_conclusion`),
- `title_ru`, `safety_domain` (enum: `occupational | industrial | labour |
  fire | environmental | road | dangerous_goods`),
- `subject_kind` (`organization | employee | asset`),
- `review_period_months` (planned review, e.g. 60 for ИОТ) **or**
  `validity_months` (for employee permits) **or** `periodicity_months`
  (recurring briefings; used by P11-005/006),
- `warning_thresholds_days` (JSON array, default `[90,30,14,7]`),
- `requires_acknowledgement` (bool), `requires_approval_order` (bool),
- `legal_basis` (free text + optional regulation reference),
- `is_active`.

Seed via a data migration or a bootstrap script (decide in planning; the
Hazard slice has no seed precedent, prefer a script under `scripts/`).

### 3. `ComplianceDocument` aggregate (organisation subject in this task)

Fields: id, organization_id, document_type_id, `subject_kind`,
`subject_id` (nullable for organisation documents), `code` (registry number,
e.g. "ИОТ-012"), `title`, `status`, `version`, `issued_at`, `effective_from`,
`next_review_at`, `approved_by_document_id` (link to an order),
`supersedes_document_id`, `applicability` (JSON: positions[], work_types[],
departments[], asset_ids[]), `source` (`manual | generated | hr_form`),
current `file` (bucket, key, size, mime, sha256, original_filename),
`notes`, created/updated.

Lifecycle (explicit transitions, same style as Risk Control):

```text
draft → approved → active → under_review → active
active → superseded (when a new version is activated with supersedes link)
draft|approved|active|superseded → archived (reason required)
```

Rules:

- `active` requires a file and `effective_from`.
- Activating a document that `supersedes` another moves the old one to
  `superseded` in the same unit of work.
- `next_review_at` is computed from `effective_from + review_period_months`
  unless explicitly set; recomputed on activation.
- `is_review_due` is a backend-computed read field (`next_review_at <= today +
  threshold`); the frontend never computes it.
- Optimistic concurrency with `expected_version` on every mutation.

### 4. File upload flow

1. `POST /api/v1/compliance-documents/{id}/files/upload-url` → presigned PUT
   + key (server-generated, ADR-0006 key scheme).
2. Client uploads directly to storage.
3. `POST /api/v1/compliance-documents/{id}/files/confirm` with sha256 and
   size; backend `head`s the object, verifies, and attaches it as the current
   file (previous file kept in `document_files` history).
4. `GET /api/v1/compliance-documents/{id}/files/current/download-url`.

Limits: allowed MIME `application/pdf`, docx, xlsx, images; max size from
settings.

### 5. REST API

```text
GET    /api/v1/document-types
GET    /api/v1/compliance-documents           (filters: type, domain, status,
                                               subject_kind, review_due, search;
                                               pagination; include_archived)
POST   /api/v1/compliance-documents
GET    /api/v1/compliance-documents/{id}
PATCH  /api/v1/compliance-documents/{id}
POST   /api/v1/compliance-documents/{id}/approve | activate | start-review |
       complete-review | archive | restore
POST   /api/v1/compliance-documents/{id}/files/upload-url | files/confirm
GET    /api/v1/compliance-documents/{id}/files/current/download-url
GET    /api/v1/compliance-documents/{id}/versions
```

Permissions: `compliance_document:read | create | update | approve |
activate | archive`. Roles: admin = all; member = read/create/update;
auditor = read. Audit events: `compliance.document.created | updated |
approved | activated | review_started | review_completed | superseded |
archived | restored | file_attached`.

### 6. Frontend — "Локальные акты"

Routes under `/knowledge/documents` (or `/compliance/documents`; decide in
planning, keep consistent with `navigation.ts`):

- Registry: columns code, title, type, domain, status, effective from, next
  review, review-due badge; filters as in the API; permission-gated create.
- Create/edit form (Zod + RHF): type, code, title, dates, applicability
  (positions/work types free-text chips for now; asset links deferred),
  approval order picker (another document of type `order`).
- Object page: header with status and lifecycle actions, properties, current
  file with download, version history, "supersedes / superseded by", activity
  (audit events), placeholder tab "Ознакомление" (populated by P11-006).
- Upload dialog implementing the presigned flow with progress and sha256
  computed client-side.

### 7. Documentation

- `docs/api/ComplianceDocumentsAPI.md`, `docs/api/DocumentTypesAPI.md`.
- `docs/architecture/ComplianceDocumentPersistence.md` (mirrors
  `RiskControlPersistence.md`).
- `docs/domain/ComplianceDocuments.md` (lifecycle, rules).
- `CLAUDE.md`: MinIO in local commands, new aggregate in the list.

---

## Backend contract notes for planning

- Do not add physical DELETE.
- Cross-organisation access → 404.
- All dates are dates (not datetimes) except audit timestamps.
- `applicability` is intentionally loose JSON in this task; P11-004/006 will
  formalise position codes once Employee exists. Document this limitation.

---

## Acceptance Criteria

- A user with `compliance_document:create` can create a document, upload a
  PDF via presigned URL, approve and activate it; the registry shows it with
  the correct review-due state computed by the backend.
- Activating a new version with `supersedes_document_id` marks the old one
  `superseded` atomically.
- Storage adapter is swappable; unit tests run with the in-memory storage;
  `pytest -m db` covers the SQLAlchemy repository and migration `0013`.
- Architecture tests pass, including the new boto3 import rule.
- Frontend `npm run verify` passes; registry/object page/create/upload have
  component tests; one E2E covers create → upload → activate.
- API docs and persistence docs exist; `CLAUDE.md` updated.

---

## Non-Goals

- Employee-subject documents from hr_form (P11-008) — the type catalog only.
- Acknowledgement obligations and review reminders (P11-006/007) — only the
  computed `is_review_due` flag.
- LLM classification of uploaded PDFs (P11-002).
- Document generation from templates (P11-003).
- Asset registry links (Asset persistence is not implemented).
- Physical deletion of storage objects.

---

## Verification

- `python -m pytest tests/api/test_compliance_documents_api.py`, domain and
  contract tests; `pytest -m db` in CI.
- `python -m ruff check .`
- `cd frontend && npm run verify`
- Manual: dev stack with MinIO; upload a real PDF; confirm the object key
  scheme and that the API container never proxies bytes.

---

## Suggested implementation phases

1. Storage port + adapters + settings + MinIO + architecture test.
2. Domain + repository contracts + in-memory repo + domain tests.
3. Migration `0013` + SQLAlchemy models/mappers/repo + db tests + seed script.
4. Application handlers + RBAC + audit + API + API tests + docs.
5. Frontend registry + object page + forms + upload + tests + E2E.

---

## Approved Implementation Plan

Approved by the product owner on 2026-10-01 (Phase 3). All planning
questions below were resolved per the recommended option. Where this plan
refines the Scope above, the plan wins.

### Planning decisions

| # | Topic | Decision |
|---|---|---|
| D1 | Seed codes | Seed exactly the Scope §2 list plus briefing types `ot_briefing_*` with `periodicity_months` (expected by P11-005). P11-008 aligns its code names during its own planning. |
| D2 | Periods | Phase 3 proposes a table of default `review_period_months` / `validity_months` / `periodicity_months`; the product owner or the OT specialist confirms it before merge. |
| D3 | SHA-256 | Client computes SHA-256 (`crypto.subtle`) before requesting the upload URL. `upload-url` receives `filename`, `content_type`, `size_bytes`, `sha256`. The presigned PUT signs `Content-Type`, `Content-Length`, and `x-amz-meta-sha256`. `confirm` performs `head` and compares size, MIME type, and the SHA-256 metadata. Limitation: the hash is client-asserted; server-side byte verification is future worker work (ADR-0007). Port signature is `create_upload_url(key, content_type, size_bytes, sha256)` instead of `max_bytes` (a presigned PUT cannot sign a maximum; the exact length is signed and checked against `STORAGE_MAX_UPLOAD_BYTES` before signing). |
| D4 | Key `{version}` segment | An immutable per-upload `upload_id` (UUID): `{organization_id}/compliance_document/{document_id}/{upload_id}/{safe_filename}`. No pending-upload table; `confirm` requires the key to start with `{organization_id}/compliance_document/{document_id}/` and the object to exist. |
| D5 | Audit event names | Keep the Scope §5 names; mark identifiers that do not match `<category>.<subject>.<action>` (`review_started`, `review_completed`, `file_attached`) with `legacy_identifier=True`, as all `risk_control` events do. |
| D6 | File attachment | Files attach only in `draft`. `approve` therefore also requires a current file. `PATCH` is allowed only in `draft`. Changing an active document means a new edition (draft with `supersedes_document_id`). |
| D7 | `complete-review` | Sets `next_review_at` = review completion date + `review_period_months`, unless the request provides an explicit `next_review_at`. |
| D8 | `restore` | Returns to the status held before archiving (`status_before_archive` is stored). Reason required (Hazard precedent). |
| D9 | `code` uniqueness | Partial unique index `(organization_id, code) WHERE status IN ('active', 'under_review')`. |
| D10 | Permissions | `start-review` → `update`; `complete-review` → `activate`; `restore` → `archive`; `upload-url`, `confirm` → `update`; `download-url`, `versions`, `GET /document-types` → `read`. |
| D11 | `is_review_due` | `next_review_at <= today + max(warning_thresholds_days)`; `today` is the UTC date from `ClockContract` in the handler; always `false` when the type has no `review_period_months` or `next_review_at` is null. |
| D12 | Frontend route | `/knowledge/documents`; navigation child "Локальные акты" under "Знания", gated by `compliance_document:read`. |
| D13 | Production rollout | Phase 1 updates `infrastructure/production/.env.example`, `compose.yml`, and `docs/infrastructure/ApplicationServerDeployment.md` (Yandex Object Storage credentials, bucket CORS). Deploy only after the bucket and keys exist. |

Additional rules inferred from the Scope and confirmed with the plan:

- Activation of a document whose type has `requires_approval_order` requires `approved_by_document_id` pointing to a same-organization document of type `order`.
- `supersedes_document_id` must reference a same-organization document of the same type in `active` or `under_review`; it moves to `superseded` in the same unit of work, with its own `compliance.document.superseded` audit record.
- References to documents of another organization fail with 422 without revealing existence.
- Download URLs set `ResponseContentDisposition=attachment` (RFC 5987 filename) and `ResponseContentType` from stored metadata.
- Dates use `datetime.date` / `sa.Date` (new pattern in the backend, mandated by this task).
- Reads are not audited (Risk Control precedent).

### Reference slices

- Backend: Risk Control (entity, `_TRANSITIONS`, `_MutatingHandler`, `run_audited_admin_operation`, registries, repositories, migration `0012`); Hazard for `restore`.
- Frontend: `features/risk-controls` (registry, object page, lifecycle actions, activity via `/admin/audit-events`), `features/hazards` (create form).

### Phases

Each phase: self-review → independent review → explicit approval. One chat per phase.

1. **Storage.** `StorageContract` (replaces the placeholder), S3 and in-memory adapters, `STORAGE_*` settings incl. `STORAGE_MAX_UPLOAD_BYTES` (default 50 MB), production validation, container wiring, `boto3` dependency, MinIO + bucket bootstrap + CORS for `localhost:3100` in `docker-compose.yml`, `boto3`/`botocore` forbidden in domain/application/contracts architecture tests, production env/compose/runbook, `CLAUDE.md` MinIO commands. Verify: adapter unit tests (in-memory, signed headers without network), settings tests, `pytest tests/architecture`, `ruff`.
2. **Domain.** `DocumentType`, `ComplianceDocument` (transitions, month arithmetic without `dateutil`, `is_review_due(as_of)`, supersede, restore), `DocumentFile`, exceptions, repository contracts, in-memory repositories, UoW. Verify: domain and contract tests.
3. **Persistence.** Migration `0013` (`document_types`, `compliance_documents`, `document_files`; CHECK constraints; D9 index; `sa.Date`), SQLAlchemy models/mappers/repositories, idempotent `scripts/seed_document_types.py --organization-id` (no audit, `bootstrap_admin` precedent), D2 table, alembic head test update. Verify: `pytest -m db`.
4. **Document types + document CRUD.** Permissions/roles, audit family `compliance`, error codes, operation ids; `GET /document-types`; `POST`/`GET`/list/`PATCH` documents with filters and `is_review_due`. Verify: API tests (cross-tenant 404, 409, 422, no DELETE, role matrix), OpenAPI, taxonomy tests.
5. **Lifecycle, files, versions.** approve / activate (atomic supersede) / start-review / complete-review / archive / restore; upload-url / confirm / download-url / versions; API, persistence, and domain docs; `CLAUDE.md` aggregate list. Verify: API end-to-end tests with in-memory storage; manual dev run with MinIO (real PDF, key scheme, no bytes through the API).
6. **Frontend registry + object page.** Feature `compliance-documents`, routes, navigation, dependency-cruiser rules, registry with URL filters, object page (status, lifecycle actions, properties, file, versions, supersedes links, activity, "Ознакомление" placeholder). Verify: component tests, `npm run verify`.
7. **Frontend form + upload.** Create/edit form (Zod + RHF, order picker), upload dialog (SHA-256, XHR progress, confirm), E2E create → upload → activate. Verify: component tests, E2E, `npm run verify`.

### Acceptance Criteria coverage

| Criterion | Phases |
|---|---|
| Create → upload → approve → activate; backend review-due state | 4, 5, 7 |
| Atomic supersede | 2, 5 (db test in 3) |
| Swappable storage; in-memory unit tests; `pytest -m db`; migration `0013` | 1, 3 |
| Architecture tests incl. `boto3` rule | 1, 4 |
| `npm run verify`, component tests, E2E | 6, 7 |
| API and persistence docs; `CLAUDE.md` | 5 (MinIO commands in 1) |

### Known risks and limitations

- Production refuses to start without `STORAGE_*` after phase 1 (D13).
- SHA-256 is client-asserted (D3).
- Browsers reach object storage directly: bucket CORS and a browser-reachable presign host are required.
- `crypto.subtle.digest` reads the whole file into memory (bounded by the size limit).
- `review_due` filtering is evaluated in Python after loading the filtered set (Risk Control `overdue_only` precedent).
- `applicability` stays loose JSON; asset links deferred; document types are seed-only; `today` is UTC; no physical deletion.
