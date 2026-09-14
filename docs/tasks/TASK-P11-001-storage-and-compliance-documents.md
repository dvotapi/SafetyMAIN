# TASK-P11-001 — Object Storage and Organisational Compliance Documents

Status: Proposed
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
