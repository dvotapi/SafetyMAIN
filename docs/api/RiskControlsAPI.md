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
`review_due_after`, `overdue_only`, `awaiting_verification`, `include_terminal`,
`search`, pagination.

`include_terminal` (bool, default `false`): when `true`, includes terminal-inactive
controls (superseded/archived/cancelled) in the listing.

Unknown values for the enum-typed filters (`status`, `hierarchy_level`,
`control_nature`, `latest_effectiveness_result`) return `422` with a
`{"loc": ["query", "<field>"], "msg": "Value must be one of: ...", "type": "value_error.enum"}`
violation, not `500`.

## Response (notable fields)

`is_overdue: bool` — backend-authoritative, computed server-side from
`RiskControl.is_overdue_for_review()`; never compute this on the client.

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
