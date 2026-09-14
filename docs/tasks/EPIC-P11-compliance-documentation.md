# EPIC P11 — Compliance Documentation, Electronic Journals, and Deadline Control

Status: **Proposed** (architecture discussed 2026-09-13; tasks await Phase 1 review)

---

## Business goal

SafetyMAIN becomes the single place where ComplEX keeps, produces, and controls
all safety documentation across seven domains: occupational safety (ОТ),
industrial safety (ПБ), labour safety (ТрБез), fire safety (ПожБ),
environmental safety, road safety (БДД), and dangerous-goods transport (ДОПОГ).

Concretely, after this epic:

1. Every local normative act (instruction, regulation, order, program, plan)
   exists in SafetyMAIN as a versioned `ComplianceDocument` with a review
   cycle, an approval order, and an applicability scope.
2. Existing PDF instructions are decomposed by an LLM into reusable, tagged
   **Knowledge Blocks**; new instructions are **assembled** from blocks for a
   specific asset, role, and process.
3. Safety journals (briefing logs, PPE issue, knowledge checks, equipment
   inspections, production control) are kept **electronically**, append-only,
   with a simple electronic signature (ПЭП) of the employee.
4. Employees are synchronised from `hr_form`; expiring permits, medical
   conclusions, briefings, and acknowledgements produce **Obligations** with
   deadlines, and the responsible people are warned in-app and by email.
5. A **registry of required local acts** derived from legislation tells the
   organisation which documents it must have, performs gap analysis, and is
   kept current from regulatory-change monitoring with human confirmation.

The business priority is **instructions and journals first**; deadline
warnings second; the legislative registry third.

## Decisions already taken (do not re-open during planning)

| Topic | Decision |
|---|---|
| Tenancy | One organisation (ComplEX). Multi-tenant code stays; integrations and seeds bind to one `organization_id` via settings. |
| Employee master data | `hr_form` is the source of truth (hire, transfer, dismissal, line manager). SafetyMAIN keeps a read-model `Employee`. |
| Personal data | Only full name, position, department, manager, hire date, and permit-type documents are copied. Passport, SNILS, INN, addresses, bank details are **never** read. |
| hr_form integration | v1: read-only PostgreSQL view exposed by hr_form. v2: push events (`hired/transferred/dismissed`) once hr_form is extended. |
| File storage | S3-compatible object storage (MinIO in dev, Yandex Object Storage in prod). hr_form files are referenced by key, never copied. |
| Warning thresholds | Defaults 90/30/14/7 days; briefings 14/7. Configurable per `DocumentType`. |
| Recipients | Employee's line manager and the occupational-safety specialist. Corporate mailboxes exist (created for blue-collar workers on demand). |
| Journal signature | Simple electronic signature (ПЭП) by the employee, governed by an internal e-document regulation. Every employee gets a minimal SafetyMAIN account. |
| LLM provider | Chat models via OpenCode Zen gateway (OpenAI-compatible, `https://opencode.ai/zen/v1/`); model chosen per task (cheap for segmentation, stronger for classification/drafting). Embeddings via Z.ai directly. Free-tier models are forbidden for internal documents. |
| Vector search | `pgvector` in the existing PostgreSQL. |
| Regulatory sources | pravo.gov.ru; Garant (lawyer's subscription — API availability to be confirmed). |
| Curators of the legislative registry | Occupational-safety specialist and the product owner (role `compliance_curator`). |

## Task sequence

| # | Task | Depends on | Delivers |
|---|---|---|---|
| P11-000 | Architecture decision records | — | ADR-0006…0010, domain foundation update, repo hygiene |
| P11-001 | Object storage + organisational compliance documents | 000 | `StorageContract`, MinIO, `DocumentType`, `ComplianceDocument`, "Local acts" UI |
| P11-002 | Knowledge Blocks: PDF decomposition pipeline | 001 | `AIProviderContract`, `EmbeddingProviderContract`, pgvector, `KnowledgeBlock`, curation UI |
| P11-003 | Instruction assembly from blocks | 002 | `DocumentTemplate`, `DocumentAssembly`, docx/pdf generation |
| P11-004 | Employee read-model + employee accounts | 001 | `Employee`, hr_form view sync, `employee` role, "People" UI |
| P11-005 | Electronic journals + simple e-signature | 004 | `Journal`, `JournalEntry`, ПЭП, printable forms, `Training` persistence |
| P11-006 | Obligations Engine | 003, 005 | `Obligation`, applicability rules, evaluation worker, "Deadlines" UI |
| P11-007 | Notifications | 006 | `Notification`, in-app inbox, email |
| P11-008 | Employee permit documents from hr_form | 004, 006 | `field_key → DocumentType` mapping, expiry obligations |
| P11-009 | Regulatory requirements registry | 006 | `RegulatoryRequirement`, `ApplicabilityRule`, `OrganizationComplianceProfile`, gap analysis |
| P11-010 | Regulatory change monitoring + AI | 009 | source watchers, AI diff, curator queue |
| P11-011 | hr_form push events | 008 + hr_form work | `POST /integrations/hr/events`, dismissal handling |

Critical path for the business priority: **000 → 001 → 002 → 003** (instructions)
and **001 → 004 → 005** (journals). 006–008 follow; 009–011 are the next horizon.

## Pre-work that needs no code

- Collect all existing PDF instructions into one folder with meaningful names
  (input to P11-002).
- List the journals currently kept on paper, with their forms (input to P11-005).
- Start the "regulation → required document" table with the OT specialist
  (input to P11-009).
- Confirm with the lawyer whether the Garant subscription includes API/export.
- Run the segmentation pilot described in P11-002 §Pilot before committing to
  the LLM-segmentation approach.

## Conventions for all P11 tasks

- Every task follows `docs/ai/DevelopmentWorkflow.md`: Phase 2 planning must
  produce an approved plan before code; implementation is phased and reviewed.
- Backend contracts are authoritative; frontend never invents endpoints,
  permissions, transitions, or calculations.
- New aggregates follow the Hazard / Risk Control vertical slice as the
  nearest completed reference (domain → application → SQLAlchemy → router →
  RBAC → audit → tests).
- New permissions go to `backend/core/domain/value_objects/permission.py` and
  role mappings to `role_permissions.py`; new audit events go to the
  `safety` (or a new `compliance`) family under
  `backend/core/domain/security_events/families/`.
- No physical DELETE endpoints. Cross-organisation access returns 404.
- UI reuses `docs/design/RegistryPattern.md` and the Object Page pattern;
  Russian copy per `docs/design/RussianUICopy.md`.
- Each task updates `CLAUDE.md` / `AI_CONTEXT.md` if it changes commands,
  structure, or conventions.
