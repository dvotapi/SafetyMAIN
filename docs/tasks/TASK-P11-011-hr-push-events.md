# TASK-P11-011 — hr_form Push Events (Hire, Transfer, Dismissal)

Status: Proposed
Epic: `docs/tasks/EPIC-P11-compliance-documentation.md`
Depends on: TASK-P11-008; hr_form extension with HR lifecycle events (separate repository work)

---

## Goal

Move employee lifecycle from hourly polling to near-real-time push: hr_form
(or its n8n workflow) calls SafetyMAIN when an employee is hired,
transferred, dismissed, or gets a new line manager. The read-only sync from
P11-004 stays as reconciliation. Dismissal immediately cancels open
obligations and pending signatures.

---

## Context

- ADR-0008 v2 defines the endpoint, integration token, idempotency by
  `event_id`, and event types.
- hr_form side: the HR cabinet will be extended with dismissal/transfer
  actions (decision 2026-09-13); n8n can call an HTTP endpoint on status
  change. The exact hr_form change is planned in the hr_form repository;
  this task delivers the SafetyMAIN half and the contract document both
  sides implement.
- P11-004 emits `EmployeeHired/Transferred/Dismissed/ManagerChanged`
  domain events from sync; push must emit the same events so downstream
  behaviour (P11-006 cancellation, P11-007 notifications) is shared.

---

## Scope

### 1. Contract (`docs/architecture/HRIntegrationContract.md`, push section)

```json
POST /api/v1/integrations/hr/events
Authorization: Bearer <integration token>
{
  "event_id": "uuid", "occurred_at": "2026-09-13T10:00:00+05:00",
  "type": "employee.hired | employee.transferred | employee.dismissed | employee.manager_changed",
  "submission_id": "uuid",
  "payload": { "position": "...", "department": "...", "manager_submission_id": "uuid|null",
               "effective_from": "2026-09-15", "dismissed_at": "2026-09-30|null" }
}
```

Responses: `202 Accepted` (queued), `200` with `duplicate: true` for a
repeated `event_id`, `401/403` for bad token, `422` for schema errors.
Events are stored in `hr_integration_events` (raw, status, processing
error) and processed by a worker job so the caller never waits on domain
logic.

### 2. Integration authentication

- `integration_tokens`: hashed token, name, scopes (`hr:events`),
  organization_id, created_by, revoked_at, last_used_at. Admin API to create
  and revoke; the token value is shown once. Requests with an integration
  token get a `SecurityContext` with a synthetic principal
  (`integration:hr_form`) and only the `hr:events` scope; no user JWT paths
  are affected. Audit: `integration.token.created | revoked`,
  `integration.hr.event_received | event_processed | event_failed`.

### 3. Processing

- Job `process_hr_events`: applies the event to `Employee` (same handlers as
  sync), emits domain events, marks the event processed; unknown
  `submission_id` triggers an immediate targeted sync of that row from the
  view before applying.
- Dismissal: cancel active obligations (`employee_dismissed`), cancel
  pending signature requests, deactivate the employee's user account
  (revoke refresh sessions — reuse the existing deactivation handler), keep
  history.
- Reconciliation: the hourly `sync_hr` continues; conflicts (event says
  dismissed, view says employed) are logged for the admin.

### 4. UI

- Admin "Интеграция с HR": tokens management, events log with processing
  status and retry.

---

## Acceptance Criteria

- Posting a `dismissed` event with a valid token cancels obligations and
  signatures and deactivates the account within one worker cycle (test with
  in-memory queue); reposting the same `event_id` is a no-op.
- Invalid or revoked tokens are rejected and audited; integration principals
  cannot call any other endpoint (security matrix).
- Contract document updated and shared with the hr_form repository.

---

## Non-Goals

- Implementing the hr_form side (tracked in the hr_form repository).
- Bidirectional sync (SafetyMAIN never writes to hr_form).

---

## Verification

API tests, job tests, security matrix, `db` tests; a manual end-to-end run
with the n8n workflow in staging documented in the completion report.

---

## Suggested implementation phases

1. Integration tokens + security context + admin API.
2. Events endpoint + storage + job.
3. Dismissal cascade + reconciliation + UI + docs.
