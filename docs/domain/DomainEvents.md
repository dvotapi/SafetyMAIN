# Safety Domain Events

Status: Active  
Date: 2026-07-24  
Task: TASK-P8-001

Related documents:

- [SafetyDomainFoundation.md](SafetyDomainFoundation.md)
- [Aggregates.md](Aggregates.md)
- [LifecycleRules.md](LifecycleRules.md)
- [AdministrativeAuditLog.md](../architecture/AdministrativeAuditLog.md)
- [SecurityEventTaxonomy.md](../architecture/SecurityEventTaxonomy.md)

---

## 1. Purpose

Domain events express meaningful Safety business state changes. They are **in-process
facts** raised by aggregates/application handlers. This task does **not** introduce a
message bus, outbox, or async consumers.

Audit recording reuses the existing immutable audit architecture. Domain events are not
a second audit store.

---

## 2. Event Shape (Foundation)

Safety domain events use:

| Field | Meaning |
|-------|---------|
| `event_id` | Unique event identity |
| `occurred_at` | UTC timestamp |
| `organization_id` | Tenant scope |
| `aggregate_type` | e.g. `hazard`, `risk` |
| `aggregate_id` | Root identity |
| `event_type` | Stable name (`hazard.created`) |
| `payload` | Allowlisted business fields only |

No raw tokens, passwords, or unrestricted free-form PII dumps.

Ordering: events from a single aggregate instance are ordered by `occurred_at` then
`event_id`. Cross-aggregate ordering is not guaranteed without a future correlation design.

---

## 3. Catalog

| Event type | Trigger | Aggregate | Payload (minimum) | Ordering | Audit implications |
|------------|---------|-----------|-------------------|----------|-------------------|
| `hazard.created` | Hazard created in Draft/Active | Hazard | hazard_id, category | Per hazard | Administrative/business audit: create |
| `hazard.activated` | Draft → Active | Hazard | hazard_id | After created | Status change audited |
| `hazard.archived` | → Archived | Hazard | hazard_id, reason? | Terminal-ish | Archive audited |
| `risk_control.created` | RiskControl created | RiskControl | control_id, code | Per control | `safety.risk_control.created` |
| `risk_control.planned` | Draft → Planned | RiskControl | control_id | After created | Planned audited |
| `risk_control.implementation_started` | → In Implementation | RiskControl | control_id | After planned | Implementation audited |
| `risk_control.implemented` | → Implemented | RiskControl | control_id | After started | Implemented audited |
| `risk_control.verified_effective` | → Verified Effective | RiskControl | control_id, result | After implemented | Effectiveness audited |
| `risk_control.verified_partially_effective` | Partial result recorded | RiskControl | control_id, result | After implemented | Distinct from effective |
| `risk_control.verified_ineffective` | → Verified Ineffective | RiskControl | control_id, result | After implemented | May recommend reassessment |
| `risk_control.suspended` / `resumed` / `superseded` / `archived` / `cancelled` | Lifecycle ops | RiskControl | control_id, reason? | — | Operational audit |
| `risk.reassessment_recommended` | Ineffective/partial/suspend signals | RiskControl | control_id, assessment_id? | Advisory only | Does not mutate assessment |
| `risk.assessed` | Ratings set / Assessed | Risk | risk_id, hazard_id, inherent/residual levels | Per risk | Assessment audited; no algorithm detail required yet |
| `risk.accepted` | Accepted by authorized role | Risk | risk_id, accepted_by | After assessed | Approval-sensitive audit |
| `control.implemented` | Control added/marked implemented | Risk | risk_id, control_id, control_type | Within risk stream | Control change audited |
| `inspection.completed` | → Completed | Inspection | inspection_id, finding_count | After in progress | Completion audited |
| `finding.created` | Finding added | Inspection | inspection_id, finding_id, severity | Within inspection | Finding audited |
| `incident.reported` | Incident created | Incident | incident_id, near_miss?, severity | Start of incident stream | High security/investigation relevance |
| `corrective_action.assigned` | → Assigned | CorrectiveAction | action_id, assignee_user_id | After open | Assignment audited |
| `corrective_action.completed` | → Completed | CorrectiveAction | action_id | Before verify | Completion audited |
| `corrective_action.verified` | → Verified | CorrectiveAction | action_id, verifier_id | Before close | Verification audited |
| `training.completed` | → Completed | Training | training_id, person_ref | — | Competency-related audit |
| `permit.issued` | → Issued | Permit | permit_id, valid_from/to | — | High-risk work audit |
| `permit.closed` | → Closed | Permit | permit_id | After issued | Close-out audited |
| `emergency.activated` | Plan/scenario activated (future ops) | EmergencyPlan | plan_id, level | — | Critical operational audit |

Additional events may be added without renaming the table above.

---

## 4. Mapping to Platform Audit

| Concern | Mechanism |
|---------|-----------|
| Who/when/what | Existing `AuditEvent` + taxonomy where security-relevant |
| Investigation | Prefer taxonomy-backed security/investigation events when criteria met |
| Domain event bus | Not implemented; handlers may record audit directly from use cases |

Do not dual-write incompatible free-form event names outside the security taxonomy registry
for **security** events. Business operational audit actions for Safety modules will be
registered when those modules are implemented (future tasks).

---

## 5. Non-Goals

- Async delivery, retries, or consumer topology
- Exactly-once cross-service messaging
- Replacing JWT/session security events
