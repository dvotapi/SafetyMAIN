# Risk Assessment Management UI

Status: Active  
Date: 2026-08-06  
Task: [TASK-P9-006](../../tasks/TASK-P9-006.md)

Related:

- [RiskAssessmentsAPI.md](../../api/RiskAssessmentsAPI.md)
- [HazardManagementUI.md](HazardManagementUI.md)
- [SharedUIComponents.md](SharedUIComponents.md)
- [AuthenticationShell.md](AuthenticationShell.md)

## Feature structure

```text
frontend/src/features/risk-assessments/
  api/           # transport + TanStack Query + boundary-safe invalidation
  components/    # form, summary, lifecycle, conflict, related controls, activity
  pages/         # Registry / Create / Object Page
  schemas/       # Zod form models
  mappers/       # DTO ↔ view/form (incl. evaluation factor round-trip)
  hooks/         # permission capabilities + lifecycle gates
  utils/         # status, URL filters, HoC, profiles, create orchestration, 422 mapping
  types/         # transport + view models
  index.ts       # public page exports only
```

Routes:

- `/safety/risk-assessments` — registry
- `/safety/risk-assessments/new` — create (`?hazardId=` supported)
- `/safety/risk-assessments/[riskAssessmentId]` — object page

## Backend endpoints used

| Operation | Method / path |
|-----------|----------------|
| List | `GET /api/v1/risk-assessments` |
| Read | `GET /api/v1/risk-assessments/{id}` |
| Create | `POST /api/v1/risk-assessments` |
| Update / submit | `PATCH /api/v1/risk-assessments/{id}` (`submit_for_review`) |
| Approve | `POST .../approve` |
| Archive | `POST .../archive` |
| Related controls | `GET /api/v1/risk-controls?risk_assessment_id=` |
| Hazard (RA-local) | `GET /api/v1/hazards`, `GET /api/v1/hazards/{id}` |
| Activity | `GET /api/v1/admin/audit-events?resource_type=RISK&resource_id=` |

No DELETE. No separate submit or supersede HTTP routes. No list sort parameters — ordering is backend-fixed (`created_at DESC`, `id DESC`).

### List filters (supported only)

`hazard_id`, `status`, `assessment_profile`, `assessed_object_type`, `include_archived`, `include_superseded`, `search`, `created_from`, `created_to`, `offset`, `limit`.

Registry UI exposes a practical subset (status, profile, archived, superseded, search, hazard chip). URL parsing still accepts the full supported set for deep links.

### Two-step create

1. `POST` with `CreateRiskAssessmentRequest` fields only (includes required `assessed_object`).
2. Optional `PATCH` for inherent/residual evaluations, proposed controls, acceptance, and other update-only fields.

If POST succeeds and PATCH fails, the Draft remains on the create page with an honest message and a **Retry saving risk details** action that performs PATCH only (never a second POST). Submit lock stays acquired after successful navigation.

## Permissions

`risk:read|create|update|approve|archive`, plus `risk_control:read` (related controls) and `audit:read` (activity).

Submit-for-review uses `risk:update` (via `submit_for_review: true`). There is no `risk:submit` permission.

Capabilities are mapped in `mapRiskAssessmentCapabilities` — never by role name.

Hazard Object Page Create CTA uses `risk:create` and requires Hazard status `active` (backend create rule).

## Product lifecycle UX

```text
Draft → Under Review → Approved → (Superseded | Archived)
```

- Edit draft fields: Draft + `risk:update`
- Submit: Draft + inherent risk present + `risk:update`
- Approve: **Under Review only** + `risk:approve` (UI product rule; backend may allow draft→approved). Approve dialog always allows confirm/override of acceptance (decision + justification).
- Archive: domain-allowed statuses + `risk:archive` + reason

Superseding is server-side on approve. Frontend invalidates/refetches lists and details; it does not invent superseded peer IDs from the approve response alone.

## Assessment profiles

There is **no** profile-list or matrix-configuration API.

The feature keeps a **minimal** catalog: `code`, `title`, `matrixSize`, `requiredFactorIds` (always includes `probability` and `severity`, plus profile-specific extras such as `business_impact`).

Authoritative risk `level` comes from the backend response. The UI collects factor scores for PATCH; it does not own risk formulas.

## Query keys and cache

Keys are scoped by `organizationId` via `riskAssessmentKeys.*` (`all`, `lists`, `list`, `details`, `detail`, `relatedControls`, `activity`).

### Boundary-safe Hazard related-RA invalidation

Hazard stores related assessments under:

```text
["hazards", organizationId, "detail", hazardId, "risk-assessments"]
```

The Risk Assessment feature **must not** import Hazard internals. Mutations invalidate that cache with predicate/prefix helpers in `api/invalidate-hazard-related.ts` (shape kept comment-synced with Hazard).

Logout clears the QueryClient through AuthProvider.

## Cross-feature integration

- Hazard → Create Risk Assessment: public route `/safety/risk-assessments/new?hazardId=…`
- Hazard related assessments: public routes `/safety/risk-assessments/{id}`
- No cross-feature internal imports (dependency-cruiser enforced)

## Optimistic concurrency

Mutations send `expected_version`. On `409 Conflict`, a feature-local conflict dialog (shared `Dialog` primitives) prompts reload without auto-retry. Edit form values are preserved when the user chooses “Keep my draft”.

## Evaluation round-trip

Response evaluations are `{ factors: [{ factor, score }], level, explanation }`.

Form models store probability/severity scores plus a map of extra factor scores.
Mappers rebuild PATCH `RiskEvaluationRequest` only when **both** probability and
severity are present, without inventing authoritative `level`.

Zod enforces profile `matrixSize` bounds and `requiredFactorIds` when an
evaluation section is non-empty.

Date-only form inputs (`YYYY-MM-DD`) are normalized to ISO datetime (`…T00:00:00Z`) for API payloads.

## Known limitations

- No profile-list/configuration API — minimal frontend catalog may drift; keep it minimal.
- **`extension_references` is deferred** — supported by the create/update API but not on the form.
- Sending `null` for `assessment_date` or `review_schedule` on PATCH does **not** clear existing values (backend treats `None` as “omit field”).
- Materialize-controls is out of UI scope; related controls may be empty while proposed controls exist (empty states distinguish “no proposed” vs “not materialized”).
- Product UI hides Draft→Approve while backend allows it.
- Registry filter UI is an intentional subset of supported list query params.

## Testing

- Unit/component: mappers, schema, permissions/lifecycle, orchestration, 422 mapping, related-controls empty kinds, approve acceptance, invalidation predicates.
- Storybook: `Features/RiskAssessments` (registry/create/object presentation, lifecycle, related controls, loading/empty/error, conflict).
- Playwright: happy path create→edit→submit→approve→archive; permission denied; validation; 409 conflict; 404 tenant masking; partial-create PATCH retry.
- Architecture: dependency-cruiser includes `risk-assessment-api-no-components` and existing cross-feature boundary rules.
