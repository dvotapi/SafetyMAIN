# Risk Assessments API

Base path: `/api/v1/risk-assessments`

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/risk-assessments` | `risk:create` |
| GET | `/api/v1/risk-assessments` | `risk:read` |
| GET | `/api/v1/risk-assessments/{id}` | `risk:read` |
| PATCH | `/api/v1/risk-assessments/{id}` | `risk:update` |
| POST | `.../{id}/approve` | `risk:approve` |
| POST | `.../{id}/archive` | `risk:archive` |

No DELETE. Cross-tenant access returns `404`.

Create requires an **active** hazard. Update may set inherent/residual evaluations,
controls, acceptance, and optionally `submit_for_review`. Approve supersedes prior
approved assessments in the same hazard/context/profile scope.
