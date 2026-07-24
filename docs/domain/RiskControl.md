# RiskControl

Independent operational control aggregate for SafetyMAIN.

## Why independent

Embedded controls inside `RiskAssessment` are immutable historical snapshots of what was
proposed/accepted during assessment. `RiskControl` tracks whether a control was
implemented, verified, remains effective, and continues to reduce risk.

## Chain

```text
Hazard → Risk Assessment → Risk Control → Implementation → Effectiveness Verification → Residual Risk Review (recommendation only)
```

## Lifecycle (implemented)

```text
Draft → Planned → In Implementation → Implemented → Verified Effective
```

Additional states: `Verified Ineffective`, `Suspended`, `Superseded`, `Archived`,
`Cancelled`. No hard DELETE.

## Materialization

`MaterializeRiskAssessmentControls` creates controls from embedded assessment measures
for Approved (default) or Under Review assessments. Uniqueness:

```text
(organization_id, risk_assessment_id, source_control_reference)
```

Source snapshots are immutable. Assessments are not mutated.

## Corrections (deferred)

**Outcome A — deferred dedicated CorrectionRecord model.**

Implemented protections today:

- verification records are append-only;
- source assessment snapshots are immutable after create;
- evidence after `Implemented` requires explicit `allow_after_implemented`;
- audit/event extension point `safety.risk_control.correction_recorded` exists.

Follow-up: `TASK-P8-HARDENING-001 — Historical Correction Records`.

## Persistence guarantees

- PostgreSQL table `risk_controls` (Alembic `0012_risk_controls`)
- Optimistic concurrency via `version`
- Tenant-scoped repository access (cross-tenant → not found)
- Restart-safe nested JSONB payloads

## Key capabilities

- Hierarchy of Controls (`ControlType`) + `ControlNature`
- Ownership with history
- Implementation plan, milestones, evidence references
- Immutable verification history + effectiveness profile key/version
- Review schedule and overdue detection via injected clock
- Competency / related entity typed references
- Extension data for country/industry profiles
