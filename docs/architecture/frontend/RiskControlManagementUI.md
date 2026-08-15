# Risk Control Management UI

Status: Active (Phase A — read-only slice)
Date: 2026-08-16
Task: [TASK-P9-007a](../../tasks/TASK-P9-007a.md) (sub-task of [TASK-P9-007](../../tasks/TASK-P9-007.md))

Related:

- [RiskControlsAPI.md](../../api/RiskControlsAPI.md)
- [RiskAssessmentManagementUI.md](RiskAssessmentManagementUI.md)
- [HazardManagementUI.md](HazardManagementUI.md)
- [SharedUIComponents.md](SharedUIComponents.md)
- [AuthenticationShell.md](AuthenticationShell.md)

## Feature structure

```text
frontend/src/features/risk-controls/
  api/           # transport + TanStack Query (list, detail, activity, RC-local Hazard/Assessment lite reads)
  components/    # summary, properties, source snapshot, implementation, evidence,
                 # effectiveness, verification history, relationships, activity
  pages/         # Registry / Object Page (read-only)
  mappers/       # DTO -> view model (risk-control-mappers.ts)
  hooks/         # permission capabilities (use-risk-control-permissions.ts)
  utils/         # status/effectiveness presentation, URL filter state
  types/         # transport DTOs (risk-control-dto.ts) + view/capability models (risk-control-types.ts)
  index.ts       # public page exports only
```

Phase A ships no `schemas/` (no forms yet — every mutation is out of scope) and no
`use-risk-control-lifecycle.ts` hook. Unit tests currently live as flat
`*.test.ts` files beside their subject rather than under `__tests__/`, matching
this feature's own convention introduced in Phase A.

Routes:

- `/safety/risk-controls` — registry
- `/safety/risk-controls/[riskControlId]` — object page

There is no `/safety/risk-controls/new` route — direct creation is not part of
the approved frontend workflow; controls originate from Risk Assessment
materialization (`TASK-P9-007c`).

## Backend endpoints used

| Operation | Method / path |
|-----------|----------------|
| List | `GET /api/v1/risk-controls` |
| Read | `GET /api/v1/risk-controls/{id}` |
| Hazard (RC-local lite read) | `GET /api/v1/hazards/{id}` |
| Risk Assessment (RC-local lite read) | `GET /api/v1/risk-assessments/{id}` |
| Activity | `GET /api/v1/admin/audit-events?resource_type=RISK_CONTROL&resource_id=` |

No create, update, or lifecycle-command endpoint is called in Phase A. No list
sort parameters are sent — ordering is backend-fixed
(`created_at DESC, id DESC`, see `risk_control_repository.py`).

### List filters (supported and wired)

`status`, `hierarchy_level`, `control_nature`, `hazard_id`, `risk_assessment_id`,
`owner_reference`, `latest_effectiveness_result`, `review_due_before`,
`review_due_after`, `overdue_only`, `awaiting_verification`, `include_terminal`,
`search`, `offset`, `limit`.

Registry UI exposes status, hierarchy level, control nature, effectiveness,
overdue-only, awaiting-verification, and include-terminal as first-class
controls; `hazard_id`, `risk_assessment_id`, `owner_reference`,
`review_due_before/after` are accepted by URL-state parsing (deep links) even
though the registry toolbar does not surface dedicated pickers for them yet.

## Permissions

`risk_control:read` gates the Registry and Object Page. Related reads use the
owning feature's own read permission: `hazard:read` for the linked Hazard
summary, `risk:read` for the linked Risk Assessment summary, `audit:read` for
the Activity tab. No write permission (`risk_control:assign`, `:implement`,
`:verify`, `:review`, `:suspend`, `:supersede`, `:archive`, `:cancel`,
`:materialize`) is consumed yet — the capability model already exposes them (see
`RiskControlCapabilities` in `types/risk-control-types.ts`) but nothing in the
UI reads them until `TASK-P9-007b`.

Capabilities are mapped in `mapRiskControlCapabilities` — never by role name.
Navigation entry (`frontend/src/lib/navigation.ts`) is gated by
`risk_control:read` via the shared permission-aware nav renderer.

## Registry behaviour

- Server-side pagination (`offset`/`limit`), default page size 25.
- **Fixed server ordering**: `created_at DESC, id DESC`. There is no sort
  column selector in the UI and no sort query parameter is ever sent — the
  Registry description text says so explicitly ("Ordering is fixed by the
  server").
- **`include_terminal` defaults to `false`.** Superseded, archived, and
  cancelled controls are hidden unless the user toggles "Include closed" (URL
  param `includeTerminal=true`), which is surfaced with an explanatory caption
  when off.
- Columns: Reference, Control, Hierarchy Level, Status, Owner, Implementation,
  Effectiveness, Hazard, Risk Assessment, Next Review, Overdue, Updated At —
  all backend-sourced; Implementation and Overdue are derived presentation
  (see below), not separate backend fields beyond `is_overdue`.
- Loading, first-use empty, filtered-empty, and error+retry states are
  distinct. Filters reset `page` to 1 on change; an out-of-range page
  self-corrects to the last valid page once `total` is known.
- Filter state round-trips through the URL (`utils/risk-control-filters.ts`);
  malformed values (unknown enums, non-numeric page/pageSize, malformed
  `YYYY-MM-DD` date filters) are dropped rather than forwarded to the API.

## Source snapshot

`SourceSnapshot` (`components/source-snapshot.tsx`) renders
`control.source.snapshot` read-only: source type, source control reference,
assessment version, assessment approved-at, residual level, and the captured
proposed-control fields (control type, description, responsible). It never
reconstructs the snapshot from the current Risk Assessment or fetches live
Risk Assessment data to backfill it — when `snapshot` is `null` (control was
not materialized), an explicit empty state is shown instead of guessing.
`SourceDto`/`RiskControlSource` allow arbitrary extra snapshot keys
(`[key: string]: unknown`) since the backend snapshot shape is
intentionally open-ended and the frontend does not enumerate every possible
proposed-control field.

## Overdue semantics

`is_overdue` is a backend-authoritative boolean added to `RiskControlResponse`
in this task's first backend patch (see Backend changes below). The frontend
never recomputes it from `next_review_date` — `mapRiskControlDto` copies it
through as `Boolean(dto.is_overdue)` and every display site (`Registry`
Overdue column, Object Page header badge) reads `control.isOverdue` directly.
Registry exposes `overdue_only` as a toggle that is sent straight through as
a query parameter; there is no client-side overdue filtering.

## Tenant isolation

Every list/detail/activity query is keyed by `organizationId` (see Query keys
below) via `useOrganization()`. A `404` from `GET /risk-controls/{id}` (used
for both "does not exist" and cross-tenant masking, per backend contract)
renders the same "Risk control not found" empty state — the frontend performs
no additional check and cannot distinguish the two cases, matching backend
masking intent. Related Hazard/Risk Assessment lite reads use `retry: false`
and are only issued when the corresponding read permission is present;
inaccessible related resources fail silently into the relevant section's own
empty/error handling rather than crashing the Object Page. Logout clears the
QueryClient through `AuthProvider`, which drops all `risk-controls`-keyed
cache entries.

## Activity source

`RiskControlActivity` reads exclusively from
`GET /api/v1/admin/audit-events?resource_type=RISK_CONTROL&resource_id=`,
gated by `audit:read` (`capabilities.canViewActivity`) and only fetched once
the detail query has succeeded. `ACTIVITY_TITLES` in `risk-control-api.ts`
maps the `safety.risk_control.*` audit event-name taxonomy to human-readable
titles, falling back to the raw event name for anything unmapped. The Activity
tab itself is only rendered when `canViewActivity` is true; no fake or
client-synthesized history is ever shown.

## Error handling

Uses the shared normalized API error model (`@/services/api/errors`):

- `404` (`NotFoundError`) on detail → "Risk control not found" empty state
  with a link back to the registry.
- `403`-derived `PermissionError` → distinct "Access denied" empty state
  (`toUserSafeMessage`).
- Any other error → `Alert` with a safe generic message plus a Retry button
  that calls `query.refetch()`.
- No write requests occur in Phase A, so `409`/`422` handling for mutations is
  not yet exercised by this slice; the shared conflict/validation
  infrastructure from Hazard/Risk Assessment is expected to be reused as-is in
  `TASK-P9-007b`.

## Query keys and cache

`riskControlKeys` (`api/risk-control-query-keys.ts`), scoped by
`organizationId`:

```text
riskControlKeys.all(orgId)
riskControlKeys.lists(orgId)
riskControlKeys.list(orgId, filters)
riskControlKeys.forAssessment(orgId, riskAssessmentId)
riskControlKeys.forHazard(orgId, hazardId)
riskControlKeys.details(orgId)
riskControlKeys.detail(orgId, riskControlId)
riskControlKeys.activity(orgId, riskControlId)
riskControlKeys.hazard(orgId, hazardId)
riskControlKeys.assessment(orgId, riskAssessmentId)
```

`forAssessment`/`forHazard` key builders exist ahead of `TASK-P9-007c`
materialization/related-list wiring but are not yet consumed by any query hook
in Phase A. Logout clears all Risk Control data through the shared
QueryClient reset in `AuthProvider`.

## Testing strategy

- Unit: `risk-control-mappers.test.ts` (DTO→view mapping, wrapped-id
  unwrapping, snapshot pass-through), `risk-control-status.test.ts` (status/
  effectiveness label and visual mapping, implementation-state derivation),
  `risk-control-permissions.test.ts` (capability mapping from permission
  strings), `risk-control-query-keys.test.ts` (key stability/tenant scoping),
  `risk-control-filters.test.ts` (URL state parse/serialize round-trip,
  malformed-input degradation, list-params translation).
- Component/integration and Storybook coverage for presentation components,
  and Playwright E2E, are out of scope for Phase A — see placeholders below.
- Architecture: dependency-cruiser rules already in place from Hazard/Risk
  Assessment (shared components never import feature code; features import
  each other only through `index.ts`) apply unchanged to `risk-controls`; no
  Phase-A-specific rule was needed since the feature makes no cross-feature
  internal imports.

---

## Materialization (Phase B/C)

Delivered in TASK-P9-007b/c.

## Owner assignment

Delivered in TASK-P9-007b.

## Implementation workflow

Delivered in TASK-P9-007b.

## Evidence

Delivered in TASK-P9-007b.

## Effectiveness verification

Delivered in TASK-P9-007b.

## Verification history (write path)

Delivered in TASK-P9-007b.

## Review scheduling

Delivered in TASK-P9-007b.

## Lifecycle actions (assign/plan/start/progress/complete/verify/review/suspend/resume/supersede/cancel/archive)

Delivered in TASK-P9-007b.

## Optimistic concurrency

Delivered in TASK-P9-007b.

## Storybook stories

Delivered in TASK-P9-007b/c.

## Browser end-to-end tests

Delivered in TASK-P9-007c.

## Known limitations

- `competency_requirements` and `related_entities` are read-only over HTTP and
  always empty; displayed but not editable.
- Suspension / cancel / archive / supersede reasons are not in the response;
  only visible via the audit API, which needs `audit:read`.
- `409` does not carry the server's current version; recovery is a re-GET.
- No employee/user directory exists — owner assignment uses the raw backend
  owner reference (see TASK-P9-007b).

## Deferred work

Delivered in TASK-P9-007b/c.
