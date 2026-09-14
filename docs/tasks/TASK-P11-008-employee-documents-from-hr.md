# TASK-P11-008 — Employee Permit Documents from hr_form

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-004 (sync, raw document rows), TASK-P11-006 (renew obligations)

---

## Goal

Turn the employee documents that hr_form already recognised (driving
licences, ДОПОГ certificates, operator licences, Rostekhnadzor and
attestation protocols, medical and psychiatric conclusions) into
`ComplianceDocument` records with validity dates, so that the Obligations
Engine warns before they expire and the employee card shows a complete
permit picture — without copying files or personal identifiers.

---

## Context

- P11-004 stores rows from `hr.safetymain_employee_documents_v` raw in
  `hr_employee_documents_raw` (`field_key`, storage bucket/key, OCR
  `number`, `issue_date`, `expiry_date`, medical `exam_date`,
  `next_exam_date`, `decision`, `verification_status`).
- hr_form OCR slots with expiry semantics (from
  `docs/medical/intake-ocr-schema.v1.json`): `driver_license`, `ekv_copy`,
  `dopog_cert`, `driver_card`, `tractor_license`, `tractor_rights`,
  `drilling_license`, `excavator_license`, `medical_cert`; protocol slots
  `rtn_protocol`, `attestation_protocol` (`protocol_date`, validity by
  rule); `hr.medical_conclusions` (`next_exam_date`).
- Employee `DocumentType` entries were seeded in P11-001 with
  `validity_months` and thresholds.
- ADR-0006 external references: files stay in `complex-hr-docs`; SafetyMAIN
  reads them with `STORAGE_EXTERNAL_*` read-only credentials via presigned
  GET.

---

## Scope

### 1. Mapping catalog

`hr_document_mappings` (seeded, admin-editable): `field_key` →
`document_type_code`, `date_rule` (`expiry_from_ocr | issue_plus_validity |
protocol_plus_validity | next_exam_date`), `min_verification_status`
(`match` by default — unverified OCR is imported as `draft`, not `active`).

### 2. Materialisation job

`materialize_hr_documents` (after each `sync_hr` run): for each raw row with a
mapping, upsert a `ComplianceDocument` with `subject_kind=employee`,
`source=hr_form`, `external_ref=hr document_id`, `code=number`,
`issued_at`, `valid_to` per `date_rule`, external file reference, status
`active` when verification is sufficient else `draft` with a "требует
проверки" flag; a newer document of the same type for the same employee
supersedes the older one. Raw rows without a mapping are listed for the
admin ("неизвестный тип").

### 3. Obligations

- `renew_document` obligations for employee documents are produced by the
  P11-006 evaluation using `valid_to`; this task adds the applicability rules
  "employees in position X must hold document type Y" for the seeded
  employee types (e.g. drivers of dangerous goods → `dopog_cert`) so that
  **missing** documents also produce obligations, not only expiring ones.
- Medical: `medical_conclusion.next_exam_date` drives a `renew_document`
  obligation of kind label "пройти периодический медосмотр".

### 4. API and UI

- `GET /api/v1/employees/{id}/documents` (documents + derived status:
  valid / expiring / expired / missing per required type — backend
  computed).
- Employee object page "Документы" tab (placeholder from P11-004): table by
  required type with status badges and file preview via presigned URL.
- Admin page: mapping catalog, unmapped `field_key`s, last materialisation
  report.
- Registry "Документы сотрудников" (subject_kind filter on the P11-001
  registry is sufficient; add the missing/expiring quick filters).

### 5. Documentation

`docs/architecture/HRIntegrationContract.md` (mapping section),
`docs/api/EmployeeDocumentsAPI.md`.

---

## Acceptance Criteria

- Seeded raw rows for a driver produce active `dopog_cert` and
  `driver_license` documents with correct `valid_to`; unverified rows land
  as `draft`; re-running changes nothing; a newer certificate supersedes the
  old one.
- A driver without a `dopog_cert` gets a `renew_document` obligation with
  "missing" origin; an expiring one gets threshold notifications through
  P11-007 (integration test with fake sender).
- Files open through presigned GET from the external bucket; no object copy
  exists in the SafetyMAIN bucket (test asserts storage calls).
- Employee "Документы" tab shows the backend-computed statuses;
  `npm run verify` passes.

---

## Non-Goals

- Reading personal identifiers from hr_form.
- Manual upload of employee documents in SafetyMAIN (allowed through the
  P11-001 flow already; no special UI here).
- Changing hr_form OCR.

---

## Verification

Job tests with fixture rows; `db` tests; API tests; frontend tests.

---

## Suggested implementation phases

1. Mapping catalog + seed + admin API.
2. Materialisation job + supersede logic + reports.
3. Applicability rules for required employee documents.
4. Employee documents API + UI + docs.
