# RiskControl Persistence

Table: `risk_controls` (Alembic `0012_risk_controls`).

## Strategy

Single-table aggregate with JSONB payloads for nested value objects (scope, owner/history,
implementation, evidence, verifications, review schedule, competencies, related entities,
source snapshot, extension_data), matching Hazard/RiskAssessment persistence style.

Denormalized query columns: `owner_reference`, `latest_effectiveness_result`,
`next_review_date`, `lifecycle_status`.

## Uniqueness

- `(organization_id, code)`
- partial unique `(organization_id, risk_assessment_id, source_control_reference)` when
  source ref present

## Concurrency and restart

- Optimistic concurrency via `version` on `save`
- Nested state survives session/engine restart (verified by DB tests)
- Stale writers reject without partial nested writes

## Repositories

`InMemoryRiskControlRepository` and `SQLAlchemyRiskControlRepository` implement
`RiskControlRepositoryContract` and share contract tests.
