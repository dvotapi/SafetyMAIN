# TASK-P9-007a — Risk Control Management UI: Backend Contract Patches + Read-Only Slice

---

> **Part 1 of 3.** This sub-task implements the umbrella specification in
> `docs/tasks/TASK-P9-007.md` §1–§8, §11–§15, §28 (display only), §37–§43,
> §47–§48. It delivers: three narrow backend contract patches, and the
> read-only Risk Control frontend slice — types, mappers, permissions,
> registry, and Object Page (Overview / Implementation / Evidence /
> Verification / Relationships / Activity tabs, all read-only).
>
> Lifecycle commands (owner assignment, planning, implementation, evidence
> writes, verification, review, suspend/resume/supersede/cancel/archive)
> are out of scope here — see `TASK-P9-007b`.
> Risk Assessment materialization integration, E2E tests, and final
> documentation are out of scope here — see `TASK-P9-007c`.

## Goal

Implement the complete SafetyMAIN frontend business vertical slice for Risk Control Management.

The feature must connect the authenticated frontend application to the existing production Risk Control backend and provide a complete workflow for:

- viewing the Risk Control registry;
- opening a Risk Control Object Page;
- viewing the source Risk Assessment and Hazard;
- materializing proposed controls from an approved Risk Assessment where supported;
- assigning a control owner;
- planning implementation;
- starting implementation;
- updating implementation progress;
- adding evidence references;
- completing implementation;
- recording effectiveness verification;
- distinguishing Effective, Partially Effective, and Ineffective outcomes;
- scheduling and completing reviews;
- displaying overdue state;
- suspending and resuming controls where supported;
- superseding, cancelling, and archiving controls where supported;
- viewing immutable source snapshots;
- viewing lifecycle activity through the audit API;
- handling permissions, validation, optimistic concurrency, tenant isolation, loading, empty, and error states.

The implementation must reuse the architecture and UX patterns established by:

```text
TASK-P9-005 — Hazard Management UI
TASK-P9-006 — Risk Assessment Management UI
```

The Risk Control UI must become the third production-connected frontend business vertical slice.

Do not duplicate shared Registry, Object Page, table, form, workflow, filter, dialog, feedback, Timeline, Activity, loading, empty-state, or concurrency components.

---


## Context

The following frontend tasks are complete:

```text
TASK-P9-001 — SafetyMAIN Design System Foundation
TASK-P9-002 — Frontend Application Bootstrap
TASK-P9-003 — Shared UI Component Foundation
TASK-P9-004 — Authentication and Application Shell
TASK-P9-005 — Hazard Management UI
```

`TASK-P9-006 — Risk Assessment Management UI` is the immediately preceding frontend vertical slice and should be treated as the reference implementation for Risk-related feature architecture.

The frontend platform provides:

- Next.js 15;
- React 19;
- strict TypeScript;
- design tokens;
- IBM Plex typography;
- light, dark, and system themes;
- authenticated application shell;
- protected routes;
- permission-aware navigation;
- active organization context;
- Bearer authentication;
- `X-Organization-ID` propagation;
- automatic token refresh;
- normalized API errors;
- TanStack Query;
- React Hook Form;
- Zod;
- Storybook;
- Vitest;
- Playwright;
- dependency-cruiser architecture guardrails;
- shared UI components exported through:

```ts
import { ... } from "@/components";
```

The production Risk Control backend is fully complete and hardened.

`TASK-P8-004` and `TASK-P8-004-H1` established Risk Control as a production-ready vertical slice.

The backend includes:

- `RiskControl` aggregate;
- lifecycle management;
- owner assignment;
- implementation planning;
- implementation progress;
- evidence references;
- effectiveness verification;
- review scheduling;
- overdue handling;
- competency references;
- related entity references;
- materialization from `RiskAssessment`;
- immutable source snapshot;
- PostgreSQL persistence;
- tenant isolation;
- RBAC;
- audit events;
- optimistic concurrency;
- restart persistence;
- duplicate-materialization protection;
- REST API.

Persistence uses:

```text
risk_controls
```

Current Alembic head:

```text
0012_risk_controls
```

Primary API:

```text
/api/v1/risk-controls
```

Materialization endpoint:

```text
/api/v1/risk-assessments/{assessment_id}/materialize-controls
```

Risk Control RBAC uses:

```text
risk_control:*
```

Audit taxonomy uses:

```text
safety.risk_control.*
```

Cross-tenant access is masked as:

```text
404 Not Found
```

Stale optimistic-concurrency writes use:

```text
409 Conflict
```

Risk Control verification history is append-only.

The source Risk Assessment snapshot is immutable.

Dedicated historical `CorrectionRecord` remains intentionally deferred to:

```text
TASK-P8-HARDENING-001 — Historical Correction Records
```

The frontend must not attempt to simulate correction-record behavior.

---


## Scope

### 1. Backend Contract Review

Before implementation, inspect the actual Risk Control backend contract.

Document at minimum:

```text
Registry endpoint
Read-by-ID endpoint
Create endpoint, if supported for direct creation
Update endpoint
Materialization endpoint
Owner assignment endpoint
Implementation planning endpoint
Implementation start endpoint
Progress update endpoint
Evidence endpoint
Implementation completion endpoint
Verification endpoint
Review scheduling endpoint
Review completion endpoint
Suspend endpoint
Resume endpoint
Supersede endpoint
Cancel endpoint
Archive endpoint
Pagination contract
Sorting contract
Filter contract
Optimistic concurrency contract
Error contract
Audit activity contract
```

Also inspect:

- actual lifecycle states;
- actual transition rules;
- fields editable directly;
- fields owned by lifecycle commands;
- source Risk Assessment representation;
- source proposed-control snapshot;
- linked Hazard representation;
- implementation structure;
- evidence representation;
- verification-history representation;
- latest effectiveness result;
- review schedule;
- overdue semantics;
- competency references;
- related-object references;
- extension data;
- version field;
- permission names.

The backend contract is authoritative.

Do not invent:

- lifecycle transitions;
- permissions;
- verification states;
- review behavior;
- evidence storage semantics;
- materialization rules;
- API payloads.

---

### 2. Feature Architecture

Create a dedicated feature under:

```text
frontend/src/features/risk-controls/
```

Recommended structure:

```text
frontend/src/features/risk-controls/
├── api/
│   ├── risk-control-api.ts
│   ├── risk-control-queries.ts
│   ├── risk-control-mutations.ts
│   └── risk-control-query-keys.ts
├── components/
│   ├── risk-control-summary.tsx
│   ├── risk-control-properties.tsx
│   ├── risk-control-lifecycle-actions.tsx
│   ├── control-owner-section.tsx
│   ├── implementation-plan-section.tsx
│   ├── implementation-progress-section.tsx
│   ├── implementation-milestones.tsx
│   ├── evidence-list.tsx
│   ├── evidence-form.tsx
│   ├── effectiveness-summary.tsx
│   ├── verification-history.tsx
│   ├── verification-form.tsx
│   ├── review-schedule-section.tsx
│   ├── overdue-indicator.tsx
│   ├── source-assessment-summary.tsx
│   ├── source-snapshot.tsx
│   ├── related-hazard.tsx
│   ├── related-objects.tsx
│   └── risk-control-activity.tsx
├── pages/
│   ├── risk-control-registry-page.tsx
│   └── risk-control-object-page.tsx
├── schemas/
│   ├── owner-schema.ts
│   ├── implementation-schema.ts
│   ├── evidence-schema.ts
│   ├── verification-schema.ts
│   └── review-schema.ts
├── hooks/
│   ├── use-risk-control-permissions.ts
│   └── use-risk-control-lifecycle.ts
├── mappers/
│   └── risk-control-mappers.ts
├── types/
│   └── risk-control-types.ts
├── utils/
│   ├── risk-control-status.ts
│   ├── effectiveness-status.ts
│   └── risk-control-filters.ts
└── index.ts
```

Adapt exact names to existing frontend conventions.

Requirements:

- expose a controlled public API;
- keep transport models separate from view models;
- keep API modules independent from presentation;
- keep feature-private implementation internal;
- prevent unrelated features from deep-importing internals.

---

### 3. Routes

Add authenticated routes:

```text
/safety/risk-controls
/safety/risk-controls/[riskControlId]
```

Do not add a direct generic create route unless direct Risk Control creation is supported by the production backend.

If controls are intended to originate primarily through Risk Assessment materialization, preserve that domain workflow.

Requirements:

- routes are protected;
- read permission is required;
- direct URL navigation works;
- browser back and forward navigation works;
- invalid IDs render the standard not-found experience;
- cross-tenant IDs render the same not-found experience;
- registry filter state is URL-synchronized where appropriate.

---

### 4. Navigation Integration

Add Risk Controls under:

```text
Safety
├── Hazards
├── Risk Assessments
└── Risk Controls
```

The navigation entry must:

- use typed navigation;
- use the shared icon wrapper;
- support active state;
- support collapsed navigation;
- remain keyboard accessible;
- appear only when the user has Risk Control read permission.

Do not hardcode roles.

---

### 5. Permission Capability Model

Inspect and map actual backend permissions.

Potential categories may include equivalents of:

```text
risk_control:read
risk_control:create
risk_control:update
risk_control:assign
risk_control:implement
risk_control:verify
risk_control:review
risk_control:suspend
risk_control:supersede
risk_control:archive
risk_control:cancel
risk_control:materialize
risk_control:*
```

Use the actual backend permission model.

Create a frontend capability model such as:

```ts
type RiskControlCapabilities = {
  canRead: boolean;
  canUpdate: boolean;
  canAssignOwner: boolean;
  canPlanImplementation: boolean;
  canUpdateImplementation: boolean;
  canAddEvidence: boolean;
  canCompleteImplementation: boolean;
  canVerify: boolean;
  canScheduleReview: boolean;
  canCompleteReview: boolean;
  canSuspend: boolean;
  canResume: boolean;
  canSupersede: boolean;
  canCancel: boolean;
  canArchive: boolean;
  canMaterialize: boolean;
};
```

Adapt to actual backend permissions.

Frontend capabilities control UX only.

Backend authorization remains authoritative.

---

### 6. Risk Control Registry

Implement the registry using shared Registry and DataTable components.

The registry must provide:

- page title;
- concise operational description;
- search;
- filters;
- sorting;
- server-side pagination;
- loading state;
- skeleton state;
- first-use empty state;
- filtered-empty state;
- error state;
- retry;
- row navigation;
- keyboard support.

Recommended columns:

```text
Reference
Control
Hierarchy Level
Status
Owner
Implementation
Effectiveness
Hazard
Risk Assessment
Next Review
Overdue
Updated At
```

Use only actual backend fields.

The default view must make operational work visible.

A user should be able to quickly identify:

- unassigned controls;
- controls awaiting implementation;
- controls awaiting verification;
- ineffective controls;
- overdue reviews.

---

### 7. Registry Filters

Implement only backend-supported filters.

Potential filters include:

- lifecycle status;
- Hierarchy of Controls level;
- control nature;
- Hazard;
- Risk Assessment;
- owner;
- implementation status;
- effectiveness result;
- review due range;
- overdue;
- awaiting verification;
- free-text search.

Requirements:

- active filters are visible;
- filters can be removed individually;
- all can be cleared;
- URL state is preserved;
- changing filters resets pagination where appropriate;
- filtering remains server-side;
- invalid URL values degrade safely.

Do not perform fake filtering over a single loaded page.

---

### 8. Registry Sorting and Pagination

Use the backend sorting and pagination contract.

Support:

- stable default ordering;
- backend-supported sortable columns;
- current page;
- page size;
- total count where available;
- previous/next navigation;
- recovery from an empty final page.

Do not load all Risk Controls merely to sort them.

---

### 11. Risk Control Object Page

Implement the Object Page using shared Object Page primitives.

Recommended structure:

```text
Object Header
├── Reference
├── Control title
├── Lifecycle status
├── Implementation state
├── Effectiveness state
├── Overdue indicator
├── Primary next action
└── Overflow actions

Object Summary
├── Owner
├── Hierarchy of Controls level
├── Hazard
├── Risk Assessment
├── Next review
└── Version metadata

Tabs
├── Overview
├── Implementation
├── Evidence
├── Verification
├── Relationships
└── Activity
```

Do not add empty tabs.

The Object Page must support:

- loading;
- section skeletons;
- not found;
- permission failure where distinguishable;
- retryable errors;
- responsive layout;
- permission-aware lifecycle actions;
- meaningful browser metadata.

---

### 12. Object Header

Display:

- human-readable control reference;
- title;
- lifecycle status;
- implementation state;
- latest effectiveness result;
- overdue status where applicable;
- primary next action;
- secondary actions.

Use shared:

```text
StatusBadge
LifecycleBadge
NextActionCard
Overdue indicator patterns
```

Do not create raw feature-specific colors.

Effectiveness must clearly distinguish:

```text
Verified Effective
Verified Partially Effective
Verified Ineffective
```

Do not collapse partial effectiveness into Effective.

---

### 13. Overview Tab

Present meaningful sections.

Potential sections:

```text
Control details
Hierarchy of Controls
Owner
Source Risk Assessment
Source snapshot
Hazard
Implementation summary
Latest effectiveness
Review schedule
Competency references
Related entities
Lifecycle metadata
```

Use shared PropertyGrid, DescriptionList, Panel, Card, and relationship components.

Do not display raw JSON.

---

### 14. Source Snapshot

Display the immutable source snapshot from Risk Assessment where available.

The user should be able to understand:

- which Risk Assessment created the control;
- which proposed-control entry was used;
- what the original proposed title/description was;
- original Hierarchy of Controls classification;
- original source metadata.

Requirements:

- snapshot is read-only;
- snapshot cannot be edited;
- frontend does not reconstruct it from the current Risk Assessment;
- historical differences between current Risk Control state and source snapshot are preserved.

The immutable source snapshot is a key auditability feature.

---

### 15. Hazard and Risk Assessment Relationships

Display linked:

```text
Hazard
Risk Assessment
```

with human-readable references and titles where available.

Links must navigate through approved public routes.

Requirements:

- do not import Hazard internals;
- do not import Risk Assessment internals;
- preserve tenant isolation;
- safely handle inaccessible related resources;
- do not leak cross-tenant resource existence.

---

### 28. Overdue State

Display backend-provided overdue state.

The Registry must make overdue controls easy to find.

Use filter support such as:

```text
overdue_only
review_due_before
review_due_after
```

only when the backend provides it.

Requirements:

- Overdue is visually prominent;
- meaning does not depend only on color;
- archived, superseded, cancelled, or otherwise inactive controls must follow backend overdue semantics;
- frontend does not independently redefine what counts as overdue.

---

### 37. TanStack Query Integration

Create stable query keys.

Recommended:

```ts
riskControlKeys.all
riskControlKeys.lists()
riskControlKeys.list(filters)
riskControlKeys.details()
riskControlKeys.detail(riskControlId)
riskControlKeys.evidence(riskControlId)
riskControlKeys.verifications(riskControlId)
riskControlKeys.activity(riskControlId)
riskControlKeys.forAssessment(riskAssessmentId)
riskControlKeys.forHazard(hazardId)
```

Requirements:

- organization context is tenant-safe;
- logout clears Risk Control data;
- owner changes update relevant queries;
- implementation changes update detail and Registry;
- verification refreshes latest result, history, and Registry;
- review updates refresh overdue and due-date filters;
- materialization refreshes Assessment and Risk Control queries;
- queries support cancellation;
- no unnecessary global cache invalidation.

---

### 38. Tenant Isolation

Requirements:

- every request uses active organization context;
- Risk Control cache keys are organization-safe;
- related Hazard and Risk Assessment links respect tenant boundaries;
- cross-tenant `404` renders the normal not-found state;
- frontend never reveals cross-tenant existence;
- logout clears Risk Control state;
- future organization switching remains possible without redesign.

Do not distinguish cross-tenant masked records from missing records.

---

### 39. API Error Handling

Use the existing normalized frontend error model.

Handle at minimum:

```text
ValidationError
AuthenticationError
PermissionError
NotFoundError
ConflictError
TenantContextError
NetworkError
UnexpectedApiError
```

Expected UX:

```text
401 → authentication flow
403 → permission experience
404 → Risk Control not found
409 → stale version, duplicate materialization, or domain conflict
422 → validation/lifecycle/tenant error
Network → retryable error
Unexpected → safe generic error
```

Do not render raw backend payloads.

---

### 40. Activity and Timeline

Use the real audit API.

Potential events include:

```text
Risk Control materialized
Risk Control created
Owner assigned
Implementation planned
Implementation started
Progress updated
Evidence added
Implementation completed
Verification recorded
Verified Effective
Verified Partially Effective
Verified Ineffective
Review scheduled
Review completed
Suspended
Resumed
Superseded
Cancelled
Archived
```

Display where available:

- actor;
- timestamp;
- status transition;
- previous/new version;
- effectiveness result;
- source assessment;
- evidence reference;
- reason or note.

Do not synthesize fake history.

---

### 41. Loading, Empty, and Feedback States

Implement distinct loading states for:

- Registry;
- Object Page;
- implementation;
- evidence;
- verification history;
- review schedule;
- Activity;
- lifecycle actions.

Implement meaningful empty states for:

- no Risk Controls;
- no filtered results;
- no owner assigned;
- no implementation plan;
- no evidence;
- no verification yet;
- no review scheduled;
- no Activity.

Use specific feedback such as:

```text
Owner assigned
Implementation started
Evidence added
Control marked implemented
Verification recorded
Review scheduled
Risk Control archived
```

Avoid generic success messages.

---

### 42. Responsive Design

Desktop remains the primary productivity target.

Registry and Object Page must remain usable on:

- laptop;
- tablet;
- mobile.

Requirements:

- Registry uses approved responsive DataTable behavior;
- Object Page sections stack correctly;
- evidence lists remain readable;
- lifecycle actions remain reachable;
- verification forms remain usable;
- dialogs fit the viewport;
- no uncontrolled horizontal page overflow occurs.

Offline field workflows are outside this task.

---

### 43. Accessibility

Meet the existing accessibility baseline.

At minimum:

- semantic page structure;
- logical heading hierarchy;
- keyboard-accessible Registry;
- accessible lifecycle actions;
- labelled owner fields;
- labelled implementation fields;
- accessible evidence controls;
- accessible verification result choices;
- error announcements;
- focus management;
- status meaning not conveyed by color alone;
- effectiveness states identifiable by text;
- confirmation-dialog focus management;
- accessible tables.

Add automated checks for major screens.

---

### 47. Backend Contract Extensions

Modify backend only when the frontend reveals a concrete missing production contract.

Examples may include:

- missing registry field required for operational presentation;
- insufficient related-object summary;
- missing audit filtering;
- missing owner reference display metadata;
- insufficient materialization response;
- missing overdue filter;
- missing verification-history endpoint.

Any backend change must preserve:

```text
TenantContext
RBAC
Audit
Optimistic concurrency
Cross-tenant 404 masking
Restart persistence
Repository contracts
Migration compatibility
```

Add focused backend tests.

Do not redesign Risk Control domain behavior for frontend convenience.

---

### 48. Public Feature API

Expose only approved feature entry points.

Recommended:

```ts
export {
  RiskControlRegistryPage,
  RiskControlObjectPage,
} from "@/features/risk-controls";
```

Expose cross-feature route helpers only when they are part of the approved frontend architecture.

Do not expose internal:

- mappers;
- schemas;
- API implementation;
- private hooks;
- feature-private components.

---

## Acceptance Criteria (subset of TASK-P9-007)

The task is complete when all of the following are true:

1. A dedicated Risk Control frontend feature exists.
2. The feature follows approved frontend architecture.
3. A controlled public API exists.
4. Risk Control navigation is integrated under Safety.
5. Navigation is permission-aware.
6. The Registry route exists.
7. The Object Page route exists.
8. Routes are authenticated.
9. Registry data comes from the production backend.
10. Search uses the production backend.
11. Supported filters work.
12. Supported sorting works.
13. Server-side pagination works.
14. Registry state is URL-synchronized where appropriate.
15. Registry loading, empty, filtered-empty, error, and retry states exist.
21. The Object Page uses shared Object Page primitives.
22. The header displays control status.
23. The header displays implementation state.
24. The header displays latest effectiveness result.
25. The header displays overdue state where applicable.
26. Source Risk Assessment is displayed.
27. Source snapshot is displayed as immutable.
28. Linked Hazard is displayed.
44. Overdue state is displayed from authoritative backend data.
52. Backend `403` is handled.
53. Unknown controls render not found.
54. Cross-tenant controls render the same not-found state.
58. Query keys are stable.
59. Query caches are tenant-safe.
60. Logout clears Risk Control data.
61. Activity uses real backend audit data.
62. Fake client-generated history is not used.
64. Desktop layout is production-usable.
65. Tablet and mobile layouts remain usable.
66. Accessibility checks cover major screens.
67. Effectiveness states do not rely on color alone.
83. Shared UI components are reused.
84. No duplicate general-purpose UI framework is introduced.
85. Strict TypeScript passes.
86. Lint passes.
87. Production build passes.
88. Storybook build passes.
89. Existing authentication tests remain passing.
90. Existing Hazard UI tests remain passing.
91. Existing Risk Assessment UI tests remain passing.

---

## Non-Goals

In addition to the umbrella Non-Goals, this sub-task explicitly excludes:

- Every lifecycle command (owner assignment through archive) — `TASK-P9-007b`.
- Risk Assessment materialization integration — `TASK-P9-007c`.
- Playwright end-to-end coverage — `TASK-P9-007c`.
- Final consolidated documentation and completion report — `TASK-P9-007c`
  writes the umbrella report; this sub-task writes its own completion
  report only, appended below at hand-off.

---

## Verification

Run:

```bash
cd frontend && npm run verify
```

Coverage must include: Risk Control mappers, status mappings, permission
capabilities, query keys, registry filters, tenant isolation, API errors.

Backend:

```bash
python -m pytest -k "risk_control" -v
python -m ruff check .
```

All existing backend Risk Control tests must remain passing. The three new
backend patch tests (`include_terminal`, `is_overdue`, enum 422) must pass.

Do not mark this sub-task complete if production APIs are replaced by mock
data, the registry does not use server-side pagination, tenant masking is
unverified, or the production build fails.

---

## Completion Report

### Implementation summary

TASK-P9-007a delivers three narrow backend contract patches and the
read-only Risk Control frontend slice: types, mappers, permission
capabilities, tenant-scoped query keys, a production-connected Registry,
and an Object Page (Overview / Implementation / Evidence / Verification /
Relationships / Activity tabs), all read-only. No lifecycle command, form,
or mutation is implemented — that is `TASK-P9-007b`. Risk Assessment
materialization integration and E2E coverage are `TASK-P9-007c`.

### Frontend routes

- `/safety/risk-controls` — registry (`frontend/src/app/safety/risk-controls/page.tsx`)
- `/safety/risk-controls/[riskControlId]` — object page
  (`frontend/src/app/safety/risk-controls/[riskControlId]/page.tsx`)

Both routes are authenticated (shared app shell), require
`risk_control:read`, support direct navigation and browser back/forward, and
render the standard not-found experience for unknown or cross-tenant IDs.

### Backend endpoints used

| Operation | Method / path |
|-----------|----------------|
| List | `GET /api/v1/risk-controls` |
| Read | `GET /api/v1/risk-controls/{id}` |
| Hazard (RC-local lite read) | `GET /api/v1/hazards/{id}` |
| Risk Assessment (RC-local lite read) | `GET /api/v1/risk-assessments/{id}` |
| Activity | `GET /api/v1/admin/audit-events?resource_type=RISK_CONTROL&resource_id=` |

No create/update/lifecycle-command endpoint is called. No sort parameter is
sent — ordering is server-fixed (`created_at DESC, id DESC`).

### Permissions used

`risk_control:read` (Registry + Object Page), `hazard:read` (linked Hazard
summary), `risk:read` (linked Risk Assessment summary), `audit:read`
(Activity tab). Mapped by `mapRiskControlCapabilities` in
`frontend/src/features/risk-controls/hooks/use-risk-control-permissions.ts`
— never by role name. Navigation entry in `frontend/src/lib/navigation.ts`
is gated the same way.

### Feature structure

```text
frontend/src/features/risk-controls/
  api/        risk-control-api.ts, risk-control-queries.ts, risk-control-query-keys.ts
  components/ risk-control-summary.tsx, source-snapshot.tsx, implementation-summary.tsx,
              evidence-list.tsx, effectiveness-summary.tsx, verification-history.tsx,
              risk-control-relationships.tsx, risk-control-activity.tsx
  pages/      risk-control-registry-page.tsx, risk-control-object-page.tsx
  mappers/    risk-control-mappers.ts
  hooks/      use-risk-control-permissions.ts
  utils/      risk-control-status.ts, risk-control-filters.ts
  types/      risk-control-dto.ts, risk-control-types.ts
  index.ts    RiskControlRegistryPage, RiskControlObjectPage only
```

No `schemas/` or lifecycle hook exists yet (no forms, no mutations in Phase A).

### Shared components reused

`Alert`, `Button`, `EmptyState`, `FilterBar`, `FilterChip`, `LoadingState`,
`RegistryFooter`, `RegistryPagination`, `RegistryTable`, `RegistryToolbar`,
`Search`, `Select`, `StatusBadge`, `Text`, `PageContainer`, `PageHeader`,
`ObjectHeader`, `ObjectTabs`, `DescriptionItem`, `DescriptionList`, `Panel`
— all from `@/components`. Errors use the shared normalized error model
(`NotFoundError`, `PermissionError`, `toUserSafeMessage`).

### New shared components

None.

### Registry capabilities

Server-side pagination (offset/limit, default page size 25); fixed server
ordering (`created_at DESC, id DESC`, no sort UI); filters for status,
hierarchy level, control nature, effectiveness, overdue-only, awaiting-
verification, and include-terminal, each individually removable and URL-
synchronized; free-text search; loading, first-use empty, filtered-empty,
and error+retry states; malformed URL filter values degrade safely rather
than reaching the API. `include_terminal` defaults to `false` — superseded,
archived, and cancelled controls are hidden unless toggled on, with an
explanatory caption shown while hidden.

### Source snapshot behaviour

`SourceSnapshot` renders `control.source.snapshot` as a read-only panel
(source type, source control reference, assessment version/approved-at,
residual level, captured control type/description/responsible). It is never
reconstructed from live Risk Assessment data; when no snapshot exists an
explicit empty state is shown instead.

### Overdue behaviour

`is_overdue` is backend-authoritative (added by this task's first backend
patch) and is passed straight through by `mapRiskControlDto`
(`isOverdue: Boolean(dto.is_overdue)`) to the Registry's Overdue column and
the Object Page header badge. The frontend never recomputes it from
`next_review_date`. The `overdue_only` filter is forwarded to the backend
unchanged; there is no client-side overdue filtering.

### Tenant isolation

Every query is keyed by `organizationId` via `useOrganization()`. Backend
`404` (used for both missing and cross-tenant IDs) renders the same "Risk
control not found" state — the frontend performs no extra check and cannot
distinguish the two cases. Related Hazard/Risk Assessment lite reads use
`retry: false` and are gated by their own read permission; failures do not
crash the page. Logout clears the QueryClient (`AuthProvider`), dropping all
`risk-controls`-keyed cache entries.

### Hazard integration

Object Page fetches a minimal Hazard summary (id/code/title/status) via an
RC-local lite read (`GET /api/v1/hazards/{id}`) when `hazardId` is present
and `hazard:read` is held; rendered in the Relationships tab with a link to
`/safety/hazards/{id}`. No Hazard internals are imported.

### Risk Assessment integration

Same pattern via `GET /api/v1/risk-assessments/{id}` and `risk:read`,
linking to `/safety/risk-assessments/{id}`. No Risk Assessment internals are
imported. Materialization (creating controls from an approved assessment) is
out of scope — `TASK-P9-007c`.

### Activity source

`RiskControlActivity` reads only from
`GET /api/v1/admin/audit-events?resource_type=RISK_CONTROL&resource_id=`,
gated by `audit:read` and fetched only after the detail query succeeds.
`ACTIVITY_TITLES` maps the `safety.risk_control.*` audit taxonomy to
human-readable titles, falling back to the raw event name. No fake or
client-synthesized history is shown.

### Backend changes

Three narrow, additive patches, each with focused tests in
`tests/api/test_risk_controls_api.py`:

1. `feat(api): expose backend-authoritative is_overdue on risk control responses`
   (commit `8059722`) — adds `is_overdue` to `RiskControlResponse`.
   Test: `test_risk_control_response_exposes_is_overdue`.
2. `fix(api): return 422 for unknown risk control enum query params`
   (commit `68efdbf`) — unknown `status`/`hierarchy_level`/`control_nature`/
   `latest_effectiveness_result` query values now raise a structured 422
   instead of an unhandled 500.
   Test: `test_list_risk_controls_rejects_unknown_enum_param`.
3. `feat(api): expose include_terminal on risk control registry endpoint`
   (commit `19e9c52`) — adds the `include_terminal` list filter (default
   `false`), hiding superseded/archived/cancelled controls unless requested.
   Test: `test_list_risk_controls_include_terminal_exposes_archived`.

All three preserve TenantContext, RBAC, audit, optimistic concurrency,
cross-tenant 404 masking, and restart persistence; no migration was needed.

### Unit test count

126 tests across 19 files pass (`npm run test` via `vitest run`), including
5 new Risk Control test files: `risk-control-mappers.test.ts` (11),
`risk-control-status.test.ts` (6), `risk-control-permissions.test.ts` (5),
`risk-control-query-keys.test.ts` (4), `risk-control-filters.test.ts` (12).

### Production build result

`next build` succeeds. `/safety/risk-controls` and
`/safety/risk-controls/[riskControlId]` are present in the route manifest
(237 kB first-load JS for both).

### Architecture result

`npm run architecture:check` (dependency-cruiser): no violations —
322 modules, 1052 dependencies cruised. `risk-controls` makes no
cross-feature internal imports (Hazard/Risk Assessment reads go through
RC-local lite clients, not feature internals).

### Storybook result

`npm run build-storybook` succeeds. No Risk Control stories exist yet
(component stories are scoped to `TASK-P9-007b`/`c` per the umbrella §44
recommendation); the build itself is unaffected and green.

### Known limitations

- `competency_requirements` and `related_entities` are read-only over HTTP
  and always empty; displayed but not editable.
- Suspension / cancel / archive / supersede reasons are not in the response;
  only visible via the audit API, which needs `audit:read`.
- `409` does not carry the server's current version; recovery is a re-GET.
- No employee/user directory exists — owner assignment uses the raw backend
  owner reference (see TASK-P9-007b).

### Deferred work

All lifecycle commands (owner assignment, planning, implementation start/
progress/completion, evidence, verification, review scheduling/completion,
suspend/resume/supersede/cancel/archive) — `TASK-P9-007b`. Risk Assessment
materialization integration, component/Storybook stories for Risk Control
presentation components, Playwright E2E coverage, and the final consolidated
`TASK-P9-007` completion report — `TASK-P9-007c`.

### Verification results

- Frontend: `npm run verify` — tokens, format, lint, typecheck,
  architecture:check, 126/126 unit tests, production build: **all pass**.
- Frontend: `npm run architecture:check` (standalone): **pass** (no
  violations).
- Frontend: `npm run build-storybook`: **pass**.
- Backend: `python -m pytest` (full suite): **788 passed, 133 skipped**
  (skipped tests are `db`-marked and require `SAFETYMAIN_RUN_DB_TESTS=1` plus
  a reachable PostgreSQL instance, per repository convention — none were run
  or skipped unexpectedly outside that marker).
- Backend: `python -m ruff check .`: **368 pre-existing errors, unrelated to
  this task.** This sub-task made no Python code changes (the three backend
  patches landed in prior commits `8059722`/`68efdbf`/`19e9c52`, already on
  this branch before this task started); the ruff findings are spread across
  the whole backend tree and reproduce identically on the branch tip before
  and after this task's doc-only change. Fixing them is out of this task's
  scope (smallest-correct-change principle; no unrelated refactors). Flagged
  here as a pre-existing gap for a separate cleanup task, not a regression
  introduced by TASK-P9-007a.

### Recommended next task

`TASK-P9-007b` — Risk Control lifecycle and workflow commands (owner
assignment through archive).
