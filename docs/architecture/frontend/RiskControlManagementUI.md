# Risk Control Management UI

Status: Complete (Phase A read-only slice + Phase B write/lifecycle slice + Phase C materialization/E2E/docs)
Date: 2026-08-16
Task: [TASK-P9-007a](../../tasks/TASK-P9-007a.md), [TASK-P9-007b](../../tasks/TASK-P9-007b.md),
[TASK-P9-007c](../../tasks/TASK-P9-007c.md) (sub-tasks of [TASK-P9-007](../../tasks/TASK-P9-007.md))

Related:

- [RiskControlsAPI.md](../../api/RiskControlsAPI.md)
- [RiskAssessmentManagementUI.md](RiskAssessmentManagementUI.md)
- [HazardManagementUI.md](HazardManagementUI.md)
- [SharedUIComponents.md](SharedUIComponents.md)
- [AuthenticationShell.md](AuthenticationShell.md)

## Feature structure

```text
frontend/src/features/risk-controls/
  api/           # transport + TanStack Query (list, detail, activity, RC-local Hazard/Assessment lite reads,
                 # lifecycle command mutations — risk-control-commands.ts, materialization mutation,
                 # boundary-safe Risk Assessment related-controls invalidation —
                 # invalidate-assessment-related.ts)
  components/    # summary, properties, source snapshot, owner, implementation plan/progress,
                 # evidence, effectiveness, verification history/form, review schedule,
                 # lifecycle actions, shared command/conflict dialog shells, relationships, activity,
                 # materialize-controls-dialog.tsx (TASK-P9-007c)
  schemas/       # react-hook-form + Zod schemas, one per command (owner, implementation,
                 # implementation-progress, evidence, verification, review, lifecycle-command)
  pages/         # Registry (read-only) / Object Page (read-only + write + terminal actions)
  mappers/       # DTO -> view model (risk-control-mappers.ts)
  hooks/         # permission capabilities + lifecycle action availability
                 # (use-risk-control-permissions.ts), command mutation hook
                 # (use-risk-control-command.ts)
  utils/         # status/effectiveness presentation, URL filter state
  types/         # transport DTOs (risk-control-dto.ts) + view/capability models (risk-control-types.ts)
  risk-controls.stories.tsx  # Storybook coverage
  index.ts       # public page + MaterializeControlsDialog exports only
```

`MaterializeControlsDialog` is exported from `index.ts` alongside the two pages —
it is the one non-page component in the public surface, because it is the
approved integration point the Risk Assessment feature uses to render a
materialization affordance without importing any other Risk Control
internal (types, mutations, mappers). Its own props (`Materializable
AssessmentStatus`, `MaterializeProposedControl`) are declared locally in the
component file as structural shapes, not re-exports of Risk Assessment
types, so neither feature imports the other's internals in either
direction.

Phase A shipped no `schemas/` (no forms yet — every mutation was out of scope).
Phase B adds one `schemas/*.ts` module per lifecycle command, each pairing a
Zod validation schema with a `*FormValuesToRequest` mapper that builds the
exact backend request DTO from validated form values — validation and DTO
shaping live together, not split across files. Unit tests continue to live
as flat `*.test.ts`/`*.test.tsx` files beside their subject (now including
`risk-control-workflow.test.tsx`, which covers every Phase B component,
schema, and the accessibility pass) rather than under `__tests__/`, matching
this feature's convention from Phase A.

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
| Assign owner | `POST /api/v1/risk-controls/{id}/assign-owner` |
| Plan implementation | `POST /api/v1/risk-controls/{id}/plan` |
| Start implementation | `POST /api/v1/risk-controls/{id}/start-implementation` |
| Update progress | `POST /api/v1/risk-controls/{id}/update-progress` |
| Add evidence | `POST /api/v1/risk-controls/{id}/evidence` |
| Complete implementation | `POST /api/v1/risk-controls/{id}/complete-implementation` |
| Record verification | `POST /api/v1/risk-controls/{id}/verify` |
| Schedule review | `POST /api/v1/risk-controls/{id}/schedule-review` |
| Complete review | `POST /api/v1/risk-controls/{id}/complete-review` |
| Suspend | `POST /api/v1/risk-controls/{id}/suspend` |
| Resume | `POST /api/v1/risk-controls/{id}/resume` |
| Supersede | `POST /api/v1/risk-controls/{id}/supersede` |
| Cancel | `POST /api/v1/risk-controls/{id}/cancel` |
| Archive | `POST /api/v1/risk-controls/{id}/archive` |

| Materialize | `POST /api/v1/risk-assessments/{assessmentId}/materialize-controls` |

No list sort parameters are sent — ordering is backend-fixed
(`created_at DESC, id DESC`, see `risk_control_repository.py`). Every
lifecycle command endpoint above is a `POST` carrying `expected_version`
(optimistic concurrency, see below); none of them uses `PATCH`/`PUT`. There
is still no direct-creation endpoint used by the frontend — controls
originate from Risk Assessment materialization.

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
the Activity tab.

Phase B wires every write permission the capability model already exposed:
`risk_control:assign` gates owner assignment, `:implement` gates planning,
starting/progressing/completing implementation, and adding evidence,
`:verify` gates recording a verification, `:review` gates scheduling and
completing a review, `:suspend` gates both suspend *and* resume (the backend
guards them with the same permission), `:supersede`/`:cancel`/`:archive` gate
their respective terminal commands, and `:materialize` gates
`MaterializeControlsDialog`'s render (the dialog renders `null` entirely
without the permission, rather than a disabled affordance). Capabilities are mapped
in `mapRiskControlCapabilities` — never by role name — and every command
button is gated on both the matching capability **and** the legal lifecycle
transition for the control's current status (see `availableLifecycleActions`
below); a capability alone never makes a button appear if the transition
itself is illegal.

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
- `409` (optimistic-concurrency conflict) on any lifecycle command →
  `RiskControlConflictDialog`. The variant is chosen from the API error
  **code**, never from the `409` status alone — both "another user changed
  this control" and "these proposed controls are already materialized"
  surface as `409` — via `riskControlConflictVariantFromCode`, matching the
  backend's `risk_control_already_materialized` code (materialization-variant
  copy is present for `TASK-P9-007c` even though nothing in Phase B triggers
  it yet). Reloading re-fetches the detail query; the failed command is never
  retried automatically.
- `422` (validation) → each command dialog's own Zod schema mirrors the
  backend's required-field and conditional rules so the common case never
  reaches the server; a `422` that does reach the client renders through the
  same `RiskControlCommandDialog` error slot (`role="alert"`) as any other
  command failure.

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
  malformed-input degradation, list-params translation), `risk-control-
  commands.test.ts` / `risk-control-command.test.tsx` / `risk-control-command-
  hook.test.tsx` (mutation request shaping, error routing to the conflict vs.
  generic-error paths).
- Component/integration: `risk-control-workflow.test.tsx` covers every Phase
  B component (owner, implementation plan/progress, evidence, verification,
  review schedule, lifecycle actions) end to end — availability gating by
  status and capability, field-level Zod validation, request-body shaping,
  and the two `complete-review` traps (see below) — plus an **Accessibility**
  block (`vitest-axe`) exercising the object page and every command/
  confirmation/conflict dialog: every control has a programmatic label, the
  verification result radio group is a real `radiogroup`/`radio` pair,
  dialogs trap focus and restore it to the button that opened them on close,
  validation errors use `role="alert"`, and effectiveness is identifiable
  from text content alone.
- Storybook: `risk-controls.stories.tsx` covers every Phase B component in
  its key states (see below) with deterministic fixtures (fixed UUIDs and
  ISO timestamps — no `Date.now()`/`Math.random()`), verified by
  `npm run build-storybook`. Dark theme and narrow-viewport variants reuse
  the existing `@storybook/addon-themes`/`addon-viewport` globals rather than
  duplicating story components.
- Unit (materialization): `materialization.test.tsx` covers request shaping
  (`control_ids: null` vs. explicit selection, `allow_under_review`),
  already-materialized checkbox disabling, all-or-nothing success toast
  content, `409`→conflict-dialog routing (both variants), `422`→inline error
  routing, and query invalidation (list + assessment related-controls).
- Playwright E2E: `e2e/risk-controls.spec.ts` — see Browser end-to-end tests
  below.
- Architecture: two feature-specific dependency-cruiser rules were added in
  `TASK-P9-007c` (`.dependency-cruiser.cjs`): `risk-control-api-no-
  components` (Risk Control `api/` must not import `@/components`,
  `risk-controls/components`, or `risk-controls/pages`) and `risk-control-
  presentation-no-fetch` (Risk Control `components`/`pages` must not import
  `@/services/api/client` directly — all transport goes through `api/`).
  These mirror the pre-existing `risk-assessment-api-no-components` rule.
  The pre-existing cross-feature rules (shared components never import
  feature code; features import each other only through `index.ts`) apply
  unchanged — `risk-controls` makes no cross-feature internal imports, and
  the Risk Assessment feature's only Risk Control import is
  `MaterializeControlsDialog` through the public `index.ts`.

---

## Materialization

`MaterializeControlsDialog` (`components/materialize-controls-dialog.tsx`)
implements `Approved Risk Assessment → Proposed Control → Materialized Risk
Control`. It is rendered from the Risk Assessment Object Page's "Related
controls" tab (`risk-assessment-object-page.tsx`), imported only through
`@/features/risk-controls`'s public `index.ts` — the Risk Assessment feature
never imports a Risk Control internal type, mapper, or mutation.

- **Trigger and gating.** The dialog renders nothing (`capabilities.
  canMaterialize` gates `risk_control:materialize`) unless the user holds the
  permission. It calls `POST /api/v1/risk-assessments/{assessmentId}/
  materialize-controls` — never `POST /api/v1/risk-controls/materialize`,
  which is not used anywhere in the frontend. Materialization is enabled
  from `approved` assessments unconditionally, and from `under_review`
  assessments only behind an explicit "Materialize from an assessment still
  under review" checkbox (`allow_under_review` in the request body) — draft,
  superseded, and archived assessments show a `BlockingReason` instead of a
  selectable list.
- **Selection.** Each proposed control from `assessment.controls` (passed in
  as the caller's own `ControlMeasure[]`, never fetched or reconstructed by
  Risk Control) renders as a checkbox. A control whose `id` already appears
  as a `source.sourceControlReference` on an existing Risk Control for this
  assessment (fetched via `GET /risk-controls?risk_assessment_id=&
  include_terminal=true`) is shown checked, disabled, and labelled "Already
  materialized" — this is a client-side UX affordance to prevent an
  avoidable 409, not the source of truth; the backend still enforces
  uniqueness. Leaving the selection empty sends `control_ids: null`, which
  the backend interprets as "materialize every eligible proposed control".
- **All-or-nothing.** The confirmation `Alert` states explicitly:
  "Materialization is all-or-nothing — if any selected control already
  exists, nothing is created." The frontend never renders a partial-success
  state because the backend transaction is atomic; on success, every
  returned `RiskControl` is written into the detail cache and the created
  controls' codes are shown in the success toast
  ("Materialized N risk control(s): RC-001, RC-002").
- **Conflict handling.** A `409` is routed through the same
  `RiskControlConflictDialog` used by every other lifecycle command.
  `riskControlConflictVariantFromCode` maps the backend's
  `risk_control_already_materialized` error code to the
  `duplicate_materialization` variant (distinct copy from the generic
  stale-version variant); this is the first place in the feature that
  variant is actually reachable end-to-end. A `422` (e.g. attempting to
  materialize from a non-approved, non-under-review assessment) renders
  inline through the same flattened-violations error path the lifecycle
  command dialogs use.
- **Refresh.** On success, `useMaterializeRiskControlsMutation` invalidates
  the Risk Control list queries (so the Registry picks up the new controls)
  and the Risk Assessment's related-controls query via
  `invalidateAssessmentRelatedControls` (`api/invalidate-assessment-
  related.ts`) — a predicate/prefix-based invalidator that matches the Risk
  Assessment feature's `["risk-assessments", organizationId, "detail", id,
  "related-controls"]` key shape by convention, without importing Risk
  Assessment's key-builder module. The assessment object itself is never
  written to client-side.
- **Focus.** Like every other dialog in this feature, it captures
  `document.activeElement` on open and restores it via `onCloseAutoFocus`,
  working around the same Radix `Dialog.Trigger`-vs-externally-controlled-
  `open` gap documented under Known limitations.

## Owner assignment

`ControlOwnerSection` (`components/control-owner-section.tsx`) renders the
current owner read-only (label, owner type, assigned-at) or an
`EmptyState` when unassigned, plus an "Assign owner" / "Change owner"
button that opens a `RiskControlCommandDialog` form
(`schemas/owner-schema.ts`: owner type, owner reference, display name,
optional reason). `POST .../assign-owner` accepts re-assignment at any
point in the lifecycle except the three terminal-inactive statuses
(`superseded`, `archived`, `cancelled`) — `OWNER_ASSIGNMENT_BLOCKED_STATUSES`
in the component mirrors that, gated additionally on
`capabilities.canAssignOwner`. There is still no employee/user directory
(see Known limitations) — the "owner reference" field is a free-text value
the backend does not validate against any directory.

## Implementation workflow

Four lifecycle commands move a control from `draft` to `implemented`,
split across two components because their legal source statuses differ:

- **`ImplementationPlanSection`** (`plan`, only from `draft`, only once an
  owner is assigned) — target dates, implementation method, resource
  notes, dependencies, evidence requirements, verification method
  requirement (conditionally required — see `implementation-schema.ts`),
  and a milestone list (`useFieldArray`, add/remove, each milestone
  requiring a title). Renders `null` once `status !== "draft"` — it never
  reappears as an "edit plan" affordance for a `planned` control; the
  backend's `PATCH` (draft/planned only) is out of scope for Phase B.
- **`ImplementationProgressSection`** bundles the remaining three:
  `start_implementation` (`planned` → `in_implementation`, no form, a plain
  `ConfirmationDialog`), `update_progress` (`in_implementation` only —
  percentage plus an optional note; milestones are shown read-only here,
  edited only through the plan), and `complete_implementation`
  (`in_implementation` → `implemented` — a required completion summary,
  plus a conditionally-required evidence-waiver reason when no evidence
  exists yet, and an "allow incomplete milestones" checkbox that only
  appears when a milestone is still pending). Completing implementation
  shows a `NextActionCard` prompting effectiveness verification as the
  next step.

## Evidence

`EvidenceList` + `EvidenceForm` (`schemas/evidence-schema.ts`) add
`add_evidence` records: evidence type, external reference, title,
description, checksum. Evidence is **always a reference** — external
system ID, document ID, or checksum — never a file; neither component ever
renders `<input type="file">` or any binary-upload affordance. `add_evidence`
is blocked on the same terminal-inactive statuses as owner assignment
(`ADD_EVIDENCE_BLOCKED_STATUSES`), gated on `capabilities.canImplement`.
Once a control has reached `implemented`/`verified_effective`/
`verified_ineffective`, adding more evidence is still legal but is treated
as a deliberate append — the form shows a warning `Alert` and requires an
explicit "Add evidence after implementation" checkbox
(`allowAfterImplemented`) before submitting.

## Effectiveness verification

`VerificationForm` (`record_verification`) is only offered from
`implemented`, `verified_effective`, or `verified_ineffective`
(`VERIFY_ALLOWED_STATUSES` — mirrored identically in
`use-risk-control-permissions.ts` as the `verify` lifecycle-action guard, so
the form's own availability check and the header lifecycle button's
availability check can never disagree). The `result` field is a `RadioGroup`
over `VERIFIABLE_RESULTS` only (`effective` / `partially_effective` /
`ineffective`) — `not_verified` and `not_applicable` are never offered as
choices because the backend always rejects them with `422` from this
endpoint. Each option renders a visible text label ("Verified Effective",
"Verified Partially Effective", "Verified Ineffective"), never color alone;
`EffectivenessSummary` and `VerificationHistory` follow the same rule when
displaying a result. Recording `partially_effective` is explicitly called
out in both the panel caption and inline near the radio group as **not**
changing the control's lifecycle status — only the effectiveness result
changes; the control's `status` field is untouched by `record_verification`
regardless of which result is chosen.

## Verification history (write path)

`VerificationHistory` renders `control.verifications` newest-first (the
backend returns the array append-only, oldest-first — the component reverses
it purely for display and tags the first rendered entry "Latest"). There is
no edit or delete control anywhere on a historical record — verification
history is append-only by construction, matching spec §51: recording a new
verification always adds a row, it never mutates or removes a prior one.

## Review scheduling

`ReviewScheduleSection` bundles `schedule_review` and `complete_review`.
**Scheduling** (`schemas/review-schema.ts`) toggles `reviewRequired`; when
on, a frequency-in-days and/or explicit next-review-date plus a review basis
and optional escalation policy reference are captured (the backend derives
`next_review_date` from `now + frequency` when only the frequency is given);
when off, a `noReviewReason` becomes mandatory. `schedule_review` is blocked
on the same terminal-inactive statuses as owner assignment/evidence
(`REVIEW_SCHEDULING_BLOCKED_STATUSES`), gated on `capabilities.canReview`.
**Completing** a review is only offered once a review is actually due
(`reviewSchedule.reviewRequired && nextReviewDate` is set) and optionally
bundles a full verification (the "record a verification as part of this
review" checkbox), reusing `buildVerificationFormSchema` unchanged rather
than re-implementing its validation. `Overdue` is read straight from
`control.isOverdue` — the backend-authoritative flag — and rendered as a
`ReviewBanner`; it is never recomputed from `nextReviewDate` client-side
because the domain rule producing it (e.g. suspended controls are never
overdue) is not reproducible on the frontend.

**`complete-review` traps** — both intentional backend quirks, documented in
`schemas/review-schema.ts` and covered by dedicated tests
(`completeReviewFormValuesToRequest`, and an end-to-end
`RiskControlObjectPage` render test):

1. **Redundant nested `expected_version`.** `CompleteReviewRequest`'s nested
   `verification` object still declares its own
   `expected_version: int = Field(ge=1)`. The backend parses and validates it
   (rejects anything `< 1`) but the `complete_review` handler never reads it
   — optimistic concurrency for the whole command is decided solely by the
   top-level `expected_version`. The frontend sets the nested value to the
   control's current version anyway purely so the request is well-formed;
   this is validated-then-ignored by design, not a bug to "fix" by removing
   the field or computing some other value for it.
2. **Double version bump.** When a `verification` is included,
   `RiskControl.complete_review` bumps the aggregate version **twice**
   server-side — once for completing the review, once more when the
   verification is applied against the already-bumped control. A control at
   version 5 can come back at version 7, not 6. The frontend never derives
   the post-command version by adding 1 (or 2) to `expectedVersion` anywhere
   — every caller reads `version` back from the mapped response
   (`mapRiskControlDto(...).version`) and renders that, never a
   client-computed value.

## Lifecycle actions (assign/plan/start/progress/complete/verify/review/suspend/resume/supersede/cancel/archive)

`RiskControlLifecycleActions` is the header "what can I do next" card.
`availableLifecycleActions` (`hooks/use-risk-control-permissions.ts`) is the
single source of truth for which actions are legal right now — it encodes
the backend's `_TRANSITIONS` table as a status→action lookup, gated on both
the legal transition **and** the matching capability, and orders the result
forward-action-first (`plan` → `start_implementation` →
`complete_implementation` → `verify` → `schedule_review`) then the five
terminal commands (`suspend`, `resume`, `supersede`, `cancel`, `archive`)
last; the first entry renders as the primary button, the rest secondary.
Never offers a delete action of any kind, for any status — `suspend` /
`cancel` / `archive` / `supersede` are all reversible-or-auditable, never
destructive.

`plan`, `start_implementation`, `complete_implementation`, `verify`, and
`schedule_review` delegate to the dialogs the object page already owns
(the sections documented above) — clicking the button in
`RiskControlLifecycleActions` only calls the page's `onPlan`/
`onStartImplementation`/etc. callback, it never opens a dialog of its own
for these five. The five terminal commands own their dialogs directly in
this component, since no other section renders them:

- **`suspend`** (from `planned`, `in_implementation`, `implemented`,
  `verified_effective`, or `verified_ineffective`) — mandatory reason, optional
  expected-resolution date.
- **`resume`** (from `suspended` only) — no form, a version-only confirm.
  Guarded by `capabilities.canSuspend`, the same permission as `suspend`
  (the backend applies one permission to both).
- **`supersede`** (from `implemented`, `verified_effective`,
  `verified_ineffective`, or `suspended`) — mandatory replacement-control-ID
  (validated as a UUID client-side) and reason. The backend does not verify
  the replacement ID belongs to an existing control — the form's
  `HelperText` says so explicitly.
- **`cancel`** (from `draft`, `planned`, `in_implementation`, or
  `suspended`) — mandatory reason.
- **`archive`** (from `draft`, `implemented`, `verified_effective`,
  `verified_ineffective`, `suspended`, `superseded`, or `cancelled` —
  notably *not* `planned` or `in_implementation`, which must resolve, be
  cancelled, or be suspended first) — mandatory reason.

Suspending/superseding/archiving all show a warning `Alert` in their dialog
making clear the action is consequential but not deletion — the control
stays readable in its history and by direct link either way.

## Optimistic concurrency

Every lifecycle command carries `expected_version` (the control's current
`version` at the time the dialog opened) in its request body — no exceptions,
including the version-only commands (`start_implementation`, `resume`) and
the reason-only commands (`cancel`, `archive`). `RiskControlCommandDialog`
surfaces the version being used directly in its header
("This action uses version N") so a stale dialog left open across a
concurrent edit is visually obvious before the user even submits. On success,
the mutation's response is written straight into the detail query cache
(`mapRiskControlDto(response).version`), never client-computed — this is
what makes the `complete-review` double-bump (see above) render correctly
without special-casing that one command. On a `409` conflict, the frontend
never retries automatically and never guesses the server's current version
(the response does not carry it, see Known limitations) — the only
recovery path is `RiskControlConflictDialog`'s "Reload latest", which
re-fetches the detail query.

## Storybook stories

`risk-controls.stories.tsx` (module-level `Meta`, deterministic fixtures —
fixed UUIDs and ISO timestamps, no `Date.now()`/`Math.random()`, following
`risk-assessments.stories.tsx`'s precedent) covers: `RiskControlSummary`;
`ControlOwnerSection` (assigned / unassigned / read-only / assignment form);
`ImplementationPlanSection` (blocked-empty / ready-to-plan / plan form);
`ImplementationProgressSection` (planned / in progress / complete);
`EvidenceList` (empty / populated / add-evidence form);
`EffectivenessSummary` (not verified / Effective / Partially Effective /
Ineffective); `VerificationHistory` (empty / multi-record);
`VerificationForm` (default / submitting); `ReviewScheduleSection`
(scheduled / none / overdue); `SourceSnapshot` (present / absent); and
`RiskControlLifecycleActions` (draft / planned / implemented / suspended /
archived / permission-limited / a narrow-viewport variant using the shared
`addon-viewport` global rather than a duplicated story). Verified by
`npm run build-storybook`.

## Browser end-to-end tests

`frontend/e2e/risk-controls.spec.ts` — 20 tests, run against a real `next
start` server with the backend replaced by Playwright route interception
(`page.route`), the same pattern `hazards.spec.ts` and `risk-assessments.
spec.ts` already use (no live FastAPI backend is required to run
`npm run test:e2e`). Grouped into four `test.describe` blocks:

- **Main workflow** (1 test): login → open an approved Risk Assessment →
  materialize a proposed control → open the created Risk Control → assign
  owner → plan implementation → start implementation → update progress →
  add evidence → complete implementation → record an Effective verification
  → schedule a review → assert the final Object Page state.
- **Effectiveness results** (3 tests): Verified Effective, Verified
  Partially Effective, and Verified Ineffective each render their own
  distinct label and hide the other two — proving the three outcomes never
  collapse into each other in a real browser, not just in component tests.
- **Negative scenarios** (11 tests): read-only user cannot mutate; no-verify-
  permission user does not see Verify; a verify-only user sees Verify but
  not implement/review actions; a review-only user sees Schedule review but
  not Verify; unknown control renders not-found; cross-tenant control
  renders the identical not-found copy; a stale mutation shows the conflict
  dialog without auto-retrying; duplicate materialization shows the
  duplicate-variant conflict dialog; an invalid lifecycle transition is
  rejected and leaves the status badge unchanged; logout clears Risk Control
  data (re-login as a different org shows no stale rows); no delete
  affordance exists on any reachable status.
- **Terminal commands** (4 tests): suspend → resume returns to the prior
  status; archive leaves the control readable by direct link; cancel moves
  the control to `cancelled`; supersede moves the control to `superseded`.

All 20 tests pass alongside the pre-existing `auth.spec.ts`, `hazards.
spec.ts`, `risk-assessments.spec.ts`, and `smoke.spec.ts` (34 total across
`npm run test:e2e`), confirming no regression in authentication, Hazard, or
Risk Assessment E2E coverage.

## Known limitations

- `competency_requirements` and `related_entities` are read-only over HTTP and
  always empty; displayed but not editable.
- Suspension / cancel / archive / supersede reasons are not in the response;
  only visible via the audit API, which needs `audit:read`.
- `409` does not carry the server's current version; recovery is a re-GET
  through `RiskControlConflictDialog`'s "Reload latest" (see Optimistic
  concurrency above).
- No employee/user directory exists — owner assignment uses the raw backend
  owner reference; the "Owner reference" field is unvalidated free text.
- Radix's `Dialog` restores focus to `Dialog.Trigger` on close by default,
  but every command/confirmation dialog in this feature is opened from a
  plain `Button` (not `Dialog.Trigger`) against externally-held `open`
  state — `context.triggerRef` is always `null`, so without an explicit
  fix focus would silently drop to `<body>` on close instead of returning
  to the button that opened the dialog. `RiskControlCommandDialog`,
  `RiskControlConflictDialog`, and `MaterializeControlsDialog` all work
  around this locally (capture `document.activeElement` on open, restore it
  via `onCloseAutoFocus`) — found and fixed during the Phase B accessibility
  pass, applied again to the Phase C materialization dialog. The shared
  `components/dialogs/*` primitives have the same gap for any other feature
  that opens a `Dialog` the same way; fixing it there is out of scope for
  this task (see Deferred work).
- No dedicated historical `CorrectionRecord` UI. Verification history is
  append-only and rendered read-only by construction (see Verification
  history above); this remains an intentional backend decision (Outcome A —
  `CorrectionRecord` deferred), not a frontend gap. Reference:
  `TASK-P8-HARDENING-001 — Historical Correction Records`.
- The "already materialized" checkbox state in `MaterializeControlsDialog`
  is derived client-side from a fresh `GET /risk-controls?risk_assessment_
  id=&include_terminal=true` fetch at dialog-open time — it is a UX
  affordance to avoid an avoidable `409`, not authoritative; a concurrent
  materialization by another user between that fetch and submit is still
  possible and is handled by the same `409` → conflict-dialog path as any
  other duplicate.

## Deferred work

Per the umbrella specification's §52 deferred-work list:

- Dedicated `CorrectionRecord` UI (→ `TASK-P8-HARDENING-001`).
- Binary evidence upload.
- Document management.
- Inspection UI.
- Finding UI.
- Corrective Action UI.
- Incident UI.
- Employee Management UI.
- Competency Management UI.
- Training UI.
- Knowledge UI.
- Organization switching.
- Offline mode.
- Bulk Risk Control editing.
- Bulk evidence upload.
- Saved registry views backed by persistence.
- Advanced analytics.
- AI control recommendations.
- AI verification decisions.
- Automatic residual-risk mutation.
- Real-time collaborative editing.
- Websocket updates.

Additionally, carried over from Phase B and still out of scope for this
feature specifically:

- Fixing the externally-controlled-dialog focus-restore gap in the shared
  `components/dialogs/*` primitives (`Dialog`, `ConfirmationDialog`,
  `WarningDialog`, etc.) rather than locally in `risk-controls` — every
  other feature that opens a `Dialog` without `Dialog.Trigger` likely has
  the same gap; a cross-feature audit would confirm the blast radius before
  deciding whether to fix it once in the shared primitive.
- An employee/user directory to replace the raw owner-reference free-text
  field.
