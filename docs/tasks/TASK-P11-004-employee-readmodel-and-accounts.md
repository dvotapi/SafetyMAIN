# TASK-P11-004 — Employee Read-Model, hr_form Sync, and Employee Accounts

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-001 (worker runtime from P11-002 or ADR-0007 minimal loop)

---

## Goal

Introduce `Employee` as a first-class, organisation-owned aggregate that is
synchronised read-only from `hr_form`, replace the "Персонал" placeholder
with a real registry and object page, and give every employee a minimal
SafetyMAIN account so that P11-005 can collect simple electronic signatures
and P11-006 can address obligations to people.

---

## Context

- `docs/domain/SafetyDomainFoundation.md` §12 deferred person masters; ADR-0008
  (P11-000) decides hr_form is the source of truth and SafetyMAIN keeps a
  read-model.
- hr_form facts (repository `dvotapi/hr_form`, local copy inspected):
  PostgreSQL schema `hr`; `hr.submissions` holds candidates with `position`,
  `department`, normalised name parts, `status` (`approved`, then medical
  stages up to `medical_fit`); `hr.submission_documents` holds file metadata
  with `field_key`; `hr.submission_extractions` holds OCR fields;
  `hr.medical_conclusions` holds `exam_date`, `decision`, `next_exam_date`.
  hr_form has **no outbound API**; writes go through n8n. A "line manager"
  field will be added to hr_form (decision 2026-09-13). Dismissals and
  transfers will also come from hr_form later (P11-011).
- Identity today: `User`, `Membership` with roles `admin | member | auditor`
  (`backend/core/domain/value_objects/role.py`), invitations by email
  (`InvitationWorkflow.md`). `AUTH_ENFORCEMENT` and refresh sessions exist.
- Frontend `/people` renders `PlaceholderSectionPage`.

---

## Scope

### 1. hr_form side (documented contract, implemented in the hr_form repo)

Specify in `docs/architecture/HRIntegrationContract.md` (created by ADR-0008,
extended here) the two views hr_form must publish:

```sql
hr.safetymain_employees_v (
  submission_id uuid, last_name text, first_name text, patronymic text,
  position text, department text, manager_submission_id uuid null,
  employment_status text,   -- 'incoming' | 'employed' | 'dismissed'
  hired_at date null, dismissed_at date null, updated_at timestamptz)

hr.safetymain_employee_documents_v (
  document_id uuid, submission_id uuid, field_key text,
  storage_bucket text, storage_key text, original_filename text,
  number text null, issue_date date null, expiry_date date null,
  exam_date date null, next_exam_date date null, decision text null,
  verification_status text, updated_at timestamptz)
```

Rows appear only for submissions in `approved`/`medical_*` statuses. No
passport, SNILS, INN, address, bank, or children data is exposed. A
dedicated DB role `safetymain_ro` has `SELECT` on these views only.

SafetyMAIN keeps a contract fixture (`tests/integration/hr_views_contract.sql`)
and a test that compares the column list with the live view when
`HR_DATABASE_URL` is configured (skipped otherwise, loudly, like `db` tests).

### 2. `Employee` aggregate

Fields: id, organization_id, `external_ref` (hr submission id, unique per
org), `last_name`, `first_name`, `patronymic`, `position_title`,
`position_code` (normalised against `tag_vocabulary` role entries from
P11-002; nullable when unmatched), `department`, `manager_employee_id`,
`status` (`incoming | active | dismissed`), `hired_at`, `dismissed_at`,
`user_id` (nullable link to the SafetyMAIN account), `sync_source`
(`hr_form | manual`), `last_synced_at`, version, timestamps.

`employee_position_history`: employee_id, position_title, department,
valid_from, valid_to, source.

Rules: employees with `sync_source=hr_form` cannot have name/position/status
edited manually (409 with a clear error); manual employees (contractors,
visitors — created by hand) are allowed and flagged. Dismissal closes open
items in later tasks (P11-006 reacts to the `EmployeeDismissed` domain event).

### 3. Sync job

Worker job `sync_hr` (hourly + manual trigger): reads both views with
`updated_at > last_watermark`, upserts employees, appends position history
when position/department changed, resolves `manager_employee_id` by
`manager_submission_id`, emits domain events `EmployeeHired`,
`EmployeeTransferred`, `EmployeeDismissed`, `EmployeeManagerChanged`.
Document rows are stored raw in `hr_employee_documents_raw` for P11-008 (this
task does not map them to `ComplianceDocument`). Sync is idempotent; a run
report (rows read, created, updated, errors) is stored and shown in the UI.

Settings: `HR_DATABASE_URL` (read-only role), `HR_SYNC_ENABLED`,
`HR_SYNC_ORGANIZATION_ID`.

### 4. Employee accounts

- New system role `employee` in `SystemRole` with permissions limited to:
  `employee:read_self`, `journal_entry:sign_self`, `acknowledgement:sign_self`,
  `obligation:read_self`, `compliance_document:read` (active documents only).
  Update `role_permissions.py` and `RoleBasedAuthorization.md`.
- Admin action `POST /api/v1/employees/{id}/invite` creates an invitation to
  the employee's corporate email with role `employee` and links the created
  user to the employee on acceptance. Bulk invite for a filtered list.
- Employees without an email are listed as "без учётной записи"; creating
  mailboxes is an operational prerequisite documented in the runbook.
- Authorisation guardrails: an `employee` can only read their own employee
  record; all other endpoints return 404 for `employee` role where
  applicable (extend the security matrix tests).

### 5. API

```text
GET  /api/v1/employees        (filters: status, department, position, has_account,
                               search; pagination)
POST /api/v1/employees        (manual, sync_source=manual)
GET  /api/v1/employees/{id}
PATCH /api/v1/employees/{id}  (manual only; email/manager for hr_form rows)
POST /api/v1/employees/{id}/invite
POST /api/v1/employees/invite-bulk
GET  /api/v1/employees/me     (employee role)
GET  /api/v1/integrations/hr/sync-runs
POST /api/v1/integrations/hr/sync-runs   (manual trigger, admin)
```

Permissions: `employee:read | create | update | invite`, `hr_sync:run`.
Audit: `people.employee.created | updated | synced | invited |
dismissed`, `integration.hr.sync_started | sync_completed | sync_failed`.

### 6. Frontend — "Персонал"

- Registry replacing the placeholder: name, position, department, status,
  manager, account state, last sync; filters; bulk invite.
- Object page: properties, position history, manager, account state,
  placeholders for "Документы" (P11-008), "Обязательства" (P11-006),
  "Журналы" (P11-005) tabs.
- Admin page "Интеграция с HR": last runs, errors, manual run.
- Employee self-view (`/me`) for the `employee` role: own card; later tasks
  add signing and obligations here. Navigation for `employee` role shows
  only "Мой профиль" and "Документы" (active local acts, read-only).

### 7. Documentation

`docs/architecture/EmployeePersistence.md`, `docs/api/EmployeesAPI.md`,
`docs/api/HRIntegrationAPI.md`, update `RoleBasedAuthorization.md`,
`SafetyDomainFoundation.md`, `ApplicationServerDeployment.md` (HR DB role,
network access from the application server to the hr_form database), `CLAUDE.md`.

---

## Acceptance Criteria

- With `HR_DATABASE_URL` pointing at a test database seeded from the contract
  fixture, `sync_hr` creates employees, position history, and manager links;
  a second run changes nothing; a changed position creates a history row and
  a `EmployeeTransferred` event.
- No personal identifier column is ever selected (test asserts the SQL text
  and the view column list).
- An invited employee can log in and sees only their own record; the security
  matrix test covers the `employee` role against every existing endpoint.
- "Персонал" registry and object page work with the pattern components;
  `npm run verify` passes; E2E covers registry → object page → invite.

---

## Non-Goals

- Mapping employee documents to `ComplianceDocument` (P11-008).
- Push events from hr_form (P11-011).
- Org chart or department registry beyond a text field.
- SSO; employees use the existing email/password login.

---

## Verification

- Domain, application, and `db` tests; contract test against the fixture;
  security matrix; `ruff`; frontend `verify` and E2E.

---

## Suggested implementation phases

1. Contract doc + fixture + settings + read-only HR connection factory.
2. Employee domain + repositories + migration + tests.
3. Sync job + run reports + events.
4. `employee` role + invite flow + security matrix updates.
5. API + audit + docs.
6. Frontend registry, object page, HR integration page, employee self-view.
