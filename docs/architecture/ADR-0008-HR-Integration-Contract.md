# ADR-0008 — HR Integration Contract

**Status:** Accepted

**Date:** 2026-09-14

**Authors:** SafetyMAIN Architecture Team

---

# Context

Epic P11 needs people inside SafetyMAIN:

- journal entries are signed by employees (ADR-0010);
- obligations are addressed to employees and their line managers (ADR-0005);
- employee permit documents and medical conclusions expire and must be renewed.

`hr_form` is the HR system of the organization. It is a separate repository with its own PostgreSQL database. It already holds:

- candidates and employees with position, department, and normalised name parts;
- employee documents with OCR-extracted fields;
- medical conclusions;
- the files themselves, in Yandex Object Storage (bucket `complex-hr-docs`).

`hr_form` has no outbound API.

Current state of SafetyMAIN:

- there is no person master; `docs/domain/SafetyDomainFoundation.md` §12 defers Employee, Contractor, and Visitor;
- identity knows `User` and `Membership` with the roles `admin`, `member`, and `auditor`; a user is not an employee;
- ADR-0001 lists Employee as an Entity.

Epic P11 has already decided:

- `hr_form` is the source of truth for hire, transfer, dismissal, and line manager;
- only full name, position, department, manager, hire date, and permit-type documents are copied;
- passport, SNILS, INN, addresses, and bank details are never read;
- one organization is served; integrations bind to one `organization_id` through settings.

---

# Decision

`hr_form` owns employee master data: hire, transfer, dismissal, position, department, and line manager.

SafetyMAIN keeps a **read-model** `Employee`.

- `Employee` is an Entity (ADR-0001) with its own UUID and `organization_id`, versioning, and audit history.
- `external_ref` holds the `hr_form` `submission_id`. It is unique within an organization.
- The UUID is the identity of an employee inside SafetyMAIN; `external_ref` is the join key to `hr_form`.
- Fields owned by `hr_form` change only through the integration. They are never edited in SafetyMAIN.
- SafetyMAIN never writes to `hr_form`.

The integration has two versions:

- **v1** — SafetyMAIN reads published views (pull);
- **v2** — `hr_form` pushes lifecycle events; v1 remains as reconciliation.

---

# Tenancy

- The integration is bound to one `organization_id` through settings.
- Every `Employee` created by the integration belongs to that organization.
- The organization is never inferred from `hr_form` data.
- Multi-tenant code, tenant isolation, and 404 masking for cross-organization access stay unchanged.

---

# Personal Data

SafetyMAIN copies only:

- full name parts;
- position and department;
- manager reference;
- hire date and employment status;
- permit-type documents: document kind (`field_key`), validity dates, document number, file reference;
- medical fitness: exam date, next exam date, and the decision on admission to work.

Rules:

- Passport, SNILS, INN, addresses, bank details, and any other personal identifier are **not** in the views and are never read.
- Document rows are limited to permit-type `field_key`s.
- Medical data is limited to dates and the admission decision. Diagnoses and examination details are never exposed.
- The medical decision is never written to audit metadata or logs (`docs/domain/SafetyDomainFoundation.md` §7).

---

# v1 — Read-Only Views

`hr_form` publishes two PostgreSQL views:

| View | Content |
|---|---|
| `hr.safetymain_employees_v` | full name parts, position, department, manager reference, hire date, employment status |
| `hr.safetymain_employee_documents_v` | document `field_key`, storage bucket and key, OCR-extracted `issue_date` / `expiry_date` / `number`, medical `exam_date` / `next_exam_date` / `decision` |

Both views identify the employee by `submission_id`.

The exact column names and types, and the technical columns synchronisation needs (row identifiers, change timestamps), are specified by P11-004. They never add personal identifiers.

Access:

- SafetyMAIN connects with a dedicated database role that has `SELECT` on these two views only.
- The role has no access to `hr_form` tables and no write privilege.
- The connection credential is a setting, separate from the SafetyMAIN database credential.
- Synchronisation runs as the `sync_hr` job in the background worker (ADR-0007) and is idempotent.

---

# Contract Versioning

The views are a versioned contract between two repositories.

- The view definition is versioned in `hr_form` as `docs/sql/013_safetymain_views.sql`.
- SafetyMAIN mirrors the column set as a contract test fixture.
- The contract test fails when the column set changes.

A change of the column set is a contract change: `hr_form` changes the view definition, and SafetyMAIN updates the fixture and the synchronisation together.

---

# v2 — Push Events

`hr_form` (or its workflow automation) pushes employee lifecycle events to:

```text
POST /api/v1/integrations/hr/events
```

- **Authentication:** an integration token, not a user JWT. A user JWT cannot call this endpoint, and an integration token cannot call any other endpoint.
- **Tenancy:** the token belongs to the organization bound to the integration.
- **Idempotency:** by `event_id`. A repeated `event_id` has no further effect.
- **Event types:** `hired`, `transferred`, `dismissed`, `manager_changed`.

Push and pull apply changes through the same application handlers and produce the same domain events. Downstream behaviour does not depend on how a change arrived.

v1 synchronisation remains as reconciliation.

The wire format, token management, and event processing are specified by P11-011.

---

# Files

Files owned by `hr_form` are referenced by bucket and key.

They are external references in the sense of ADR-0006:

- read-only for SafetyMAIN;
- never copied into SafetyMAIN-owned buckets;
- fetched with a dedicated read-only credential.

The `hr_form` key scheme is kept as is.

---

# Employee Lifecycle and Retention

- A dismissed employee stays in the read-model with a dismissed status.
- `Employee` records are never physically deleted. Journal entries, signatures, and obligations keep referencing them.
- The effects of a dismissal on obligations, pending signatures, and the employee's account are decided by the implementing tasks (P11-006, P11-011).

---

# Principles

- `hr_form` owns people; SafetyMAIN reads.
- Copy only the data compliance needs.
- The views are a versioned, tested contract.
- Push accelerates; pull reconciles.
- Files are referenced, never copied.
- Integration credentials are separate from user credentials.

---

# Consequences

- P11-004 introduces the `Employee` read-model, the read-only `hr_form` connection and its settings, the `sync_hr` job, the contract fixture and test, and employee accounts (ADR-0010).
- P11-008 turns synchronised document rows into `ComplianceDocument` records with validity dates.
- P11-011 introduces the push endpoint and integration tokens. Integration tokens are a new authentication path; they must not weaken user authentication and are limited to the HR events endpoint.
- The manager reference requires the line manager field that `hr_form` plans to add. Production operation of the v1 synchronisation and of the manager reference depends on `hr_form` publishing the views and that field; SafetyMAIN implementation proceeds against the contract fixture. P11-011 depends on the `hr_form` push extension.
- The application server needs network access to the `hr_form` database. `docs/infrastructure/ApplicationServerDeployment.md` is updated by P11-004.
- When `hr_form` is unreachable, `sync_hr` fails in the worker and the read-model stays at the last successful synchronisation. API requests are not affected (ADR-0007).
- Audit metadata of synchronisation and push contains identifiers and counts only, never names or medical decisions.
- The Employee person master is no longer deferred. Contractor and Visitor person masters and chemical inventory remain deferred.

---

# Related ADRs

- ADR-0001 Entity-Centric Architecture
- ADR-0005 Obligations Engine
- ADR-0006 Document and Evidence Storage
- ADR-0007 Background Worker and Scheduling
- ADR-0010 Electronic Journals and Simple Electronic Signature

---

# Decision Summary

`hr_form` owns employee master data; SafetyMAIN keeps a read-model `Employee` with its own UUID and `external_ref` = `submission_id`.

v1 reads two `SELECT`-only views that expose no personal identifiers; v2 adds idempotent push events authenticated by an integration token.

The views are a versioned contract guarded by a contract test.

Files stay in `hr_form` storage and are referenced, never copied.
