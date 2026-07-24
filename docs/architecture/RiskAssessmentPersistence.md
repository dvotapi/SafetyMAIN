# Risk Assessment Persistence

Status: Implemented (TASK-P8-003)

## Table

`risk_assessments` — Alembic revision `0011_risk_assessments`.

## Storage choices

- Scalar columns for identity, scope keys, status, version, timestamps
- JSONB for `inherent_risk`, `residual_risk`, `controls`, `acceptance`,
  `review_schedule`, `competency_requirements`, `extension_references`
- FK to `organizations` and `safety_hazards`
- Unique `(organization_id, code)`
- Optimistic concurrency via `version`
- Scope index on organization + hazard + profile + assessed object + status

Trade-off: JSONB keeps nested evaluation payloads flexible for configurable
factors; primary list filters use typed scalar columns and indexes.

Repositories never commit; Unit of Work owns transactions.
