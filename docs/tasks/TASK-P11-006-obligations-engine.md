# TASK-P11-006 — Obligations Engine

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-003 (documents, applicability), TASK-P11-005 (journals, Training)

---

## Goal

Implement ADR-0005 as running code: a persistent `Obligation` aggregate, a
deterministic applicability layer that derives what each subject must have
or do, a daily evaluation job that creates, updates, and overdues
obligations, and a "Сроки" workspace. Journals, trainings, and documents
become evidence that closes obligations and schedules the next one.

Obligation kinds in this task:

| kind | subject | due date source | evidence |
|---|---|---|---|
| `acknowledge_document` | employee | document activation + N days | signed acknowledgement entry |
| `complete_training` (briefing / knowledge check) | employee | previous `Training.expires_at` or hire date + grace | `Training` completed |
| `renew_document` | employee / organisation | `ComplianceDocument.valid_to` | new active document of same type |
| `review_document` | organisation | `next_review_at`, or a stale block, or a regulation change (P11-010) | new document version activated |
| `develop_document` | organisation | set by curator (P11-009 gap analysis) | document activated |

---

## Context

- ADR-0005 structure and lifecycle: Draft → Active → In Progress →
  Completed | Cancelled | Overdue. ADR-0004 triggers: entity events,
  scheduled evaluation, date expiration.
- Worker runtime from ADR-0007 (delivered by P11-002 or here — see planning).
- Applicability data available after earlier tasks: `ComplianceDocument.
  applicability` (positions, work types, departments), `Employee.position_code`
  / `department`, `DocumentType.periodicity_months / validity_months /
  review_period_months / warning_thresholds_days / requires_acknowledgement`,
  `Training.expires_at`, `DocumentAssembly.stale_items`.
- Acknowledgement of a document is recorded as a journal entry of a new
  journal type `acknowledgement` (reuse P11-005 machinery; the printable
  form is the acknowledgement sheet template from P11-003).

---

## Scope

### 1. Applicability rules (ADR-0004 first slice)

- `applicability_rules`: id, org, `target_kind` (`document_type |
  compliance_document`), `target_id`, `conditions` (JSON: any-of position
  codes, department codes, work-type codes, hazard-factor codes,
  `all_employees` flag), `status`, version, `legal_basis`.
- A pure application service `resolve_required_items(employee) ->
  list[RequiredItem]` and `resolve_required_items_for_organization()`;
  deterministic, covered by table-driven tests. Rules referencing
  `compliance_document` are auto-created from `applicability` when a
  document is activated (kept in sync on update).
- Admin API/UI to view and edit rules per document type (simple JSON-backed
  form; the full rules engine UI is out of scope).

### 2. `Obligation` aggregate

Fields: id, org, `kind`, `subject_kind` (`employee | organization`),
`subject_id`, `target_kind`/`target_id` (document type, document, training
type), `title_ru`, `due_at`, `grace_days`, `status` (`active | in_progress |
completed | overdue | cancelled`), `priority`, `responsible_employee_id`
(defaults: the subject employee's manager for employee obligations; the
safety specialist — an org setting — for organisation obligations),
`evidence` (JSON list of refs: journal entry, training, document),
`completed_at`, `origin` (`rule | manual | gap_analysis | regulation_change`),
`dedupe_key` (unique per org: kind + subject + target + period), version.

Transitions per ADR-0005; `overdue` is set by evaluation when `due_at <
today` and not completed; completing an `overdue` obligation is allowed and
recorded as late. Cancellation requires reason. Optimistic concurrency.

Domain events: `ObligationCreated`, `ObligationDueSoon(threshold)`,
`ObligationOverdue`, `ObligationCompleted` — consumed by P11-007.

### 3. Evaluation job

`evaluate_obligations` (daily + on-demand + reacting to events
`ComplianceDocumentActivated`, `TrainingCompleted`, `EmployeeHired`,
`EmployeeTransferred`, `EmployeeDismissed`, `JournalEntrySigned`):

- For every active employee: required items → ensure an obligation exists
  per `dedupe_key` for the current period; compute `due_at` from the source
  in the table above; attach evidence and complete when satisfied; create
  the next-period obligation for recurring kinds after completion.
- For the organisation: review-due documents, stale assemblies, documents
  with `valid_to`.
- Threshold crossings: for each active obligation and each threshold in the
  target type's `warning_thresholds_days`, emit `ObligationDueSoon` exactly
  once per threshold (store `notified_thresholds`).
- Dismissed employees: cancel their active obligations with reason
  `employee_dismissed`.
- The job is idempotent and writes a run report.

### 4. API

```text
GET  /api/v1/obligations   (filters: kind, status, subject, responsible,
                            due_before/after, overdue, due_within_days,
                            document_type; sort by due_at; pagination)
GET  /api/v1/obligations/{id}
POST /api/v1/obligations                    (manual, curator)
POST /api/v1/obligations/{id}/start | complete (evidence refs) | cancel (reason)
PATCH /api/v1/obligations/{id}              (responsible, due_at for manual/organisation)
GET  /api/v1/me/obligations                 (employee role)
GET  /api/v1/obligations/summary            (counts by status/kind/threshold — backend computed)
GET/POST/PATCH /api/v1/applicability-rules
POST /api/v1/obligations/evaluate           (admin; enqueue)
```

Permissions: `obligation:read | manage`, `obligation:read_self`,
`applicability_rule:manage`. Audit: `compliance.obligation.*`.

### 5. Frontend — "Сроки"

- Registry with quick filters: просрочено / 7 дней / 30 дней / 90 дней,
  by kind, by department, by responsible; summary tiles from `/summary`.
- Object page: subject, target document/type, due date, evidence list with
  links, lifecycle actions, activity.
- Document object page "Ознакомление" tab (placeholder from P11-001): who
  must acknowledge, who has, who is overdue — from obligations.
- Employee object page "Обязательства" tab; employee `/me/obligations`.
- Applicability rules admin page.

### 6. Documentation

`docs/architecture/ObligationsEngine.md` (implements ADR-0005; job design;
dedupe; thresholds), `docs/api/ObligationsAPI.md`,
`docs/api/ApplicabilityRulesAPI.md`, `docs/domain/Obligations.md`, `CLAUDE.md`.

---

## Acceptance Criteria

- Activating a document with applicability "position = машинист буровой"
  creates `acknowledge_document` obligations for all active employees with
  that position and none for others; hiring a new such employee later
  creates one for them; a signed acknowledgement entry completes it.
- A signed repeated-briefing entry completes the current
  `complete_training` obligation and creates the next one with `due_at` =
  `Training.expires_at`.
- Evaluation run twice on the same day changes nothing (idempotency test);
  threshold events fire once per threshold.
- Overdue detection and dismissal cancellation are covered by tests with a
  controllable clock (the repo's `infrastructure/time` abstraction).
- Registry, object page, and tabs work; `npm run verify`; E2E: activate
  document → obligation appears for employee → employee signs → obligation
  completed.

---

## Non-Goals

- Email or in-app delivery (P11-007; this task only emits events and stores
  `notified_thresholds`).
- Regulation-derived required documents (P11-009 supplies `develop_document`
  obligations through the same API).
- A general rules DSL/UI beyond the JSON conditions form.

---

## Verification

Table-driven tests for applicability; evaluation tests with fake clock and
in-memory repos; `db` tests for dedupe uniqueness; security matrix for
`read_self`; frontend tests and E2E.

---

## Suggested implementation phases

1. Applicability rules + resolver + tests.
2. Obligation domain + repos + migration + events.
3. Evaluation job + event subscriptions + run reports.
4. API + RBAC + audit + docs.
5. Frontend workspace and tabs.
