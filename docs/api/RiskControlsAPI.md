# Risk Controls API

Base: `/api/v1/risk-controls`

## Routes (implemented)

- `POST /` create
- `GET /` list
- `GET /{id}` get
- `PATCH /{id}` update (draft/planned details only)
- Lifecycle: `assign-owner`, `plan`, `start-implementation`, `progress`, `evidence`,
  `complete-implementation`, `verifications`, `schedule-review`, `complete-review`,
  `suspend`, `resume`, `supersede`, `archive`, `cancel`

Materialize: `POST /api/v1/risk-assessments/{assessment_id}/materialize-controls`

No DELETE. Cross-tenant access → 404.

## Filters (implemented)

`status`, `hierarchy_level`, `control_nature`, `hazard_id`, `risk_assessment_id`,
`owner_reference`, `latest_effectiveness_result`, `review_due_before`,
`review_due_after`, `overdue_only`, `awaiting_verification`, `search`, pagination.

## RBAC

Permissions: `risk_control:read|create|update|assign|implement|verify|review|suspend|supersede|archive|cancel|materialize`

## Audit

Taxonomy: `safety.risk_control.*` (legacy identifiers registered).

## Errors

| Condition | HTTP |
|-----------|------|
| Not found / cross-tenant | 404 |
| Validation / invalid transition | 422 |
| Version conflict / already materialized / duplicate code | 409 |
| Permission denied | existing auth response |
