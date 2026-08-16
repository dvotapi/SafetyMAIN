# TASK-P9-007 — Risk Control Management UI

> **Split for execution.** This task ships as three sequential sub-tasks:
> `TASK-P9-007a` (backend contract patches + read-only slice),
> `TASK-P9-007b` (lifecycle & workflow commands),
> `TASK-P9-007c` (materialization, guardrails, E2E, documentation).
> This document remains the umbrella specification and the location of the
> final consolidated completion report.

---

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

### 9. Risk Assessment Integration

Extend the Risk Assessment Object Page where necessary.

When an approved assessment contains proposed controls:

- show materialization state;
- show `Materialize Controls` when permitted and valid;
- allow selection of supported proposed controls where the backend supports selected materialization;
- do not mutate the Risk Assessment locally;
- call the production materialization endpoint;
- refresh assessment-related controls after success;
- refresh Risk Control Registry data;
- prevent duplicate-materialization UX where backend state indicates an already materialized control;
- handle `409 Conflict`.

The Risk Assessment feature must not import Risk Control internals.

Integration must use public feature boundaries.

---

### 10. Materialization Workflow

Implement the frontend workflow for:

```text
Approved Risk Assessment
→ Proposed Control
→ Materialized Risk Control
```

Requirements:

- materialization is available only when backend lifecycle rules permit;
- permission is checked;
- selected proposed controls are clearly identified;
- show confirmation before creating production controls;
- explain that materialization creates operational Risk Control records;
- preserve immutable source snapshots;
- do not modify proposed-control history client-side;
- display created Risk Control identifiers after success where returned;
- refresh authoritative queries;
- handle duplicate conflicts;
- handle transaction failure safely;
- do not show partial success unless the backend explicitly defines it.

If the backend materializes multiple controls atomically, the UI must reflect all-or-nothing behavior.

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

### 16. Owner Assignment

Implement owner assignment using the real backend contract.

Requirements:

- show current owner;
- expose assignment only when permitted;
- use a dedicated action rather than generic property editing when the backend models assignment as a command;
- support the real owner-reference structure;
- include expected version;
- map validation errors;
- show loading state;
- refresh detail and registry after success;
- record activity through the audit API.

If no directory/employee selector exists yet:

- use the actual backend-supported owner input;
- do not implement Employee Management;
- document the limitation;
- do not create fake employees.

---

### 17. Implementation Planning

Implement the planning workflow supported by the backend.

Potential fields include:

- implementation plan;
- target date;
- responsible party;
- milestones;
- notes;
- dependencies.

Use only real backend-supported fields.

Requirements:

- valid only in allowed lifecycle states;
- permission-aware;
- use RHF and Zod;
- include expected version;
- map backend errors;
- update Object Page and Registry after success;
- preserve previous historical implementation data where the backend does.

Do not store planning data only in frontend state.

---

### 18. Start Implementation

Implement the actual command for beginning implementation where supported.

Requirements:

- show only when lifecycle permits;
- permission-aware;
- show confirmation where appropriate;
- include expected version;
- update lifecycle and implementation state after backend confirmation;
- display specific success feedback;
- record Activity through real audit events.

Do not optimistically invent state transitions.

---

### 19. Implementation Progress

Implement progress updates using actual backend fields.

Potential data:

- percentage;
- stage;
- completed milestones;
- progress note;
- implementation date;
- blocking reason.

Use only actual contract fields.

Requirements:

- prevent invalid values;
- show current progress;
- allow update only when lifecycle permits;
- include expected version;
- handle `409`;
- update registry and Object Page;
- preserve completed history where the backend exposes it.

Do not infer implementation completeness from arbitrary percentages unless the backend contract defines it.

---

### 20. Implementation Milestones

If milestones exist in the backend:

- display ordered milestones;
- show completion status;
- show due date;
- allow permitted milestone updates;
- preserve backend ordering;
- use accessible progress presentation.

If milestones are not supported, do not invent them.

---

### 21. Evidence

Implement evidence-reference management.

The production Risk Control model stores evidence information according to the actual backend contract.

Requirements:

- display existing evidence;
- add evidence when permitted;
- validate evidence type and reference;
- support evidence description/notes where available;
- show actor and timestamp where returned;
- include expected version if required;
- refresh Evidence and Activity after success;
- evidence remains persisted after page refresh;
- do not store binary files directly unless the backend already supports file upload.

If current evidence stores only references:

```text
Do not implement binary upload.
```

Future file storage belongs to a separate task.

---

### 22. Complete Implementation

Implement the command for marking implementation complete where supported.

Requirements:

- appear only when prerequisites and lifecycle permit;
- permission-aware;
- clearly explain consequences;
- validate required evidence or completion fields when backend requires them;
- include expected version;
- refresh Object Page and Registry;
- show the next expected action, typically effectiveness verification;
- never infer completion only from frontend progress state.

---

### 23. Effectiveness Verification

Implement the production effectiveness verification workflow.

Support actual backend verification fields, potentially including:

- verification result;
- verifier;
- verification method;
- evidence references;
- notes;
- verification date;
- recommendation;
- next action.

At minimum, preserve the distinct outcomes:

```text
Effective
Partially Effective
Ineffective
```

Frontend display language must follow the Design System:

```text
Verified Effective
Verified Partially Effective
Verified Ineffective
```

Requirements:

- verify only when lifecycle permits;
- permission-aware;
- use RHF + Zod;
- include expected version;
- preserve previous verification records;
- never overwrite history client-side;
- refresh latest effectiveness and history;
- show specific feedback.

---

### 24. Verification History

Display append-only verification history.

Each record should show available data such as:

```text
Result
Verifier
Method
Evidence
Timestamp
Notes
Recommendation
```

Requirements:

- newest/latest result is clearly identifiable;
- historical records remain accessible;
- records are read-only;
- frontend never offers direct editing of historical verification;
- do not simulate `CorrectionRecord`.

Dedicated corrections remain deferred.

---

### 25. Ineffective Control UX

When the latest verification is:

```text
Ineffective
```

the Object Page must clearly communicate that the control requires attention.

Use:

- semantic critical status;
- explanatory text;
- Next Action pattern where possible;
- related Risk Assessment navigation where relevant.

Do not automatically mutate residual risk.

Do not automatically create a new Risk Assessment unless the backend explicitly supports such a workflow.

The frontend may recommend reassessment only when this is supported by existing domain/audit semantics.

---

### 26. Partially Effective Control UX

Treat:

```text
Partially Effective
```

as a distinct state.

Do not map it to:

```text
Effective
```

or:

```text
Ineffective
```

Display it consistently in:

- Object Header;
- Registry;
- Verification tab;
- Activity;
- filters.

---

### 27. Review Scheduling

Implement review scheduling using actual backend fields.

Potential fields:

- next review date;
- review interval;
- review reason;
- reviewer;
- review-required flag.

Requirements:

- permission-aware;
- lifecycle-aware;
- include expected version;
- show next review clearly;
- refresh registry and Object Page;
- use backend-calculated review state where available.

Do not use browser-local calculations as authoritative compliance state.

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

### 29. Review Completion

Implement completing a scheduled review where supported.

Requirements:

- permission-aware;
- lifecycle-aware;
- collect required outcome or notes;
- include expected version;
- use actual backend command;
- update next review state;
- refresh Activity;
- preserve review history if returned by the backend.

Do not implement arbitrary review history if the backend does not expose it.

---

### 30. Suspend and Resume

Implement `Suspend` and `Resume` if supported by the real lifecycle.

Requirements:

- use explicit lifecycle commands;
- show only valid actions;
- permission-aware;
- collect reason where required;
- include expected version;
- show confirmation for suspend;
- refresh detail and Registry after success;
- preserve historical state through Activity.

Do not expose these actions if the backend does not support them.

---

### 31. Supersede

Implement superseding where supported.

Requirements:

- use a consequential-action confirmation;
- require permission;
- collect reason or replacement reference when required;
- include expected version;
- keep the control historically accessible;
- update Registry and Object Page;
- do not treat superseding as deletion.

---

### 32. Cancel

Implement cancellation where supported.

Requirements:

- show only when lifecycle permits;
- permission-aware;
- require confirmation;
- collect reason where required;
- include expected version;
- preserve historical accessibility;
- refresh relevant queries.

Do not expose hard DELETE.

---

### 33. Archive

Implement archival where supported.

Requirements:

- show only when valid;
- permission-aware;
- use confirmation;
- include expected version;
- preserve read-only historical accessibility;
- refresh Registry and detail;
- do not present archive as deletion.

---

### 34. No DELETE

The frontend must not expose a delete action for Risk Controls.

There must be no:

```text
Delete Risk Control
```

button, menu action, route, or API call.

Lifecycle terminal states remain the supported removal mechanism:

```text
Cancelled
Superseded
Archived
```

where the backend supports them.

---

### 35. Lifecycle Visualization

Use the shared workflow components only when they accurately represent the actual lifecycle.

Display:

- current state;
- completed state where meaningful;
- next valid action;
- blocked reason;
- implementation status;
- verification status;
- review status.

Risk Control contains multiple operational dimensions.

Do not force all state into a single simplistic linear stepper if that misrepresents the domain.

Prefer separate summaries for:

```text
Lifecycle
Implementation
Verification
Review
```

when needed.

---

### 36. Optimistic Concurrency

Every mutation must use the backend optimistic-concurrency contract.

On:

```text
409 Conflict
```

the UI must:

- preserve unsaved input where practical;
- explain that the control changed elsewhere;
- offer to load the latest state;
- invalidate/refetch authoritative queries;
- never silently overwrite changes;
- never automatically retry mutation commands;
- distinguish duplicate materialization from stale-version conflict when error metadata permits.

Reuse the established conflict UX.

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

### 44. Storybook

Add stories for feature presentation components that do not require a live backend.

Recommended:

```text
RiskControlSummary
ControlOwnerSection
ImplementationPlanSection
ImplementationProgressSection
EvidenceList
EffectivenessSummary
VerificationHistory
VerificationForm
ReviewScheduleSection
SourceAssessmentSummary
SourceSnapshot
RiskControlLifecycleActions
```

Include states:

- default;
- loading;
- empty;
- read-only;
- unassigned;
- implementation planned;
- in progress;
- implemented;
- Effective;
- Partially Effective;
- Ineffective;
- overdue;
- archived;
- permission-limited;
- dark theme;
- narrow viewport.

Use deterministic fixtures.

---

### 45. Unit and Integration Tests

Add unit tests for:

- API/view model mapping;
- status mapping;
- effectiveness mapping;
- permission capabilities;
- query keys;
- registry filter serialization;
- URL parsing;
- lifecycle action availability;
- owner request mapping;
- implementation request mapping;
- evidence mapping;
- verification mapping;
- review mapping;
- conflict handling;
- duplicate-materialization handling.

Add integration/component tests for:

- Registry;
- filtering;
- pagination;
- Object Page;
- source snapshot;
- owner assignment;
- implementation planning;
- implementation start;
- progress update;
- evidence addition;
- implementation completion;
- effectiveness verification;
- verification history;
- review scheduling;
- overdue state;
- lifecycle actions;
- `403`;
- `404`;
- `409`;
- Activity.

Avoid tests that only assert implementation details.

---

### 46. Browser End-to-End Tests

Add Playwright coverage.

Required main scenario:

```text
Login
→ Open approved Risk Assessment
→ Materialize proposed control
→ Open Risk Control
→ Assign owner
→ Plan implementation
→ Start implementation
→ Update progress
→ Add evidence
→ Complete implementation
→ Record effectiveness verification
→ Schedule review
→ Verify final Object Page state
```

Required effectiveness scenarios:

```text
Verify Effective
Verify Partially Effective
Verify Ineffective
```

Confirm that all three remain distinct.

Required negative scenarios:

```text
Read-only user cannot mutate
User without verification permission cannot verify
Unknown control returns 404
Cross-tenant control returns 404
Stale mutation displays conflict UX
Duplicate materialization displays conflict UX
Invalid lifecycle action is rejected
Logout clears Risk Control data
```

Where supported, include:

```text
Suspend → Resume
Archive
Cancel
Supersede
```

Tests must:

- use stable organizations;
- use stable users/permissions;
- use real Risk Assessment fixtures;
- avoid test-order dependency;
- isolate created state.

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

### 49. Architecture Guardrails

Extend architecture checks to ensure:

```text
shared components do not import risk-controls
risk-controls may import shared components
risk-controls do not import Hazard internals
risk-controls do not import Risk Assessment internals
Hazard does not import Risk Control internals
Risk Assessment does not import Risk Control internals
routes use feature public APIs
API modules do not import presentation components
presentation components do not call fetch directly
transport types do not leak into shared components
approved shared UI wrappers are not bypassed
```

Cross-feature integration must use public boundaries.

---

### 50. Documentation

Create:

```text
docs/architecture/frontend/RiskControlManagementUI.md
docs/tasks/TASK-P9-007.md
```

Update Risk Assessment frontend documentation where materialization integration changes it.

The architecture document must cover:

- feature structure;
- routes;
- API endpoints;
- query keys;
- permission model;
- Registry behavior;
- Risk Assessment materialization;
- source snapshot;
- owner assignment;
- implementation workflow;
- evidence;
- effectiveness verification;
- verification history;
- review scheduling;
- overdue semantics;
- lifecycle actions;
- optimistic concurrency;
- tenant isolation;
- Activity;
- testing strategy;
- known limitations;
- deferred work.

The completion report must include:

```text
Implementation summary
Frontend routes
Backend endpoints used
Permissions used
Feature structure
Shared components reused
New shared components
Registry capabilities
Materialization workflow
Source snapshot behavior
Owner assignment
Implementation workflow
Evidence behavior
Effectiveness verification
Review scheduling
Overdue behavior
Lifecycle actions
Optimistic concurrency
Hazard integration
Risk Assessment integration
Activity source
Backend changes
Unit test count
E2E test count
Storybook result
Production build result
Architecture result
Known limitations
Deferred work
Recommended next task
```

---

### 51. Correction Record Boundary

Do not implement dedicated historical correction records in this task.

Current backend decision remains:

```text
Outcome A — CorrectionRecord deferred
```

Verification history is append-only.

Source snapshots are immutable.

The frontend must:

- display historical verification as read-only;
- not provide Edit/Delete for historical verification records;
- not simulate historical rewriting;
- not invent correction-record workflows.

Reference:

```text
TASK-P8-HARDENING-001 — Historical Correction Records
```

as deferred work where relevant.

---

### 52. Deferred Work

Explicitly defer:

```text
Dedicated CorrectionRecord UI
Binary evidence upload
Document management
Inspection UI
Finding UI
Corrective Action UI
Incident UI
Employee Management UI
Competency Management UI
Training UI
Knowledge UI
organization switching
offline mode
bulk Risk Control editing
bulk evidence upload
saved registry views backed by persistence
advanced analytics
AI control recommendations
AI verification decisions
automatic residual-risk mutation
real-time collaborative editing
websocket updates
```

Do not expand this task into Inspection Management.

---

## Acceptance Criteria

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

16. Risk Assessment materialization uses the production endpoint.

17. Materialization is permission-aware.

18. Duplicate materialization handles `409`.

19. Materialization does not mutate Risk Assessment state client-side.

20. Created Risk Controls appear in related views.

21. The Object Page uses shared Object Page primitives.

22. The header displays control status.

23. The header displays implementation state.

24. The header displays latest effectiveness result.

25. The header displays overdue state where applicable.

26. Source Risk Assessment is displayed.

27. Source snapshot is displayed as immutable.

28. Linked Hazard is displayed.

29. Owner assignment works.

30. Owner assignment is permission-aware.

31. Implementation planning works.

32. Implementation start works where supported.

33. Implementation progress updates work.

34. Implementation completion works.

35. Evidence can be added using the backend contract.

36. Existing evidence is displayed.

37. Binary upload is not invented when unsupported.

38. Effectiveness verification works.

39. Effective is distinct from Partially Effective.

40. Partially Effective is distinct from Ineffective.

41. Verification history is append-only in the UI.

42. Historical verification cannot be edited.

43. Review scheduling works.

44. Overdue state is displayed from authoritative backend data.

45. Review completion works where supported.

46. Suspend/Resume works where supported.

47. Supersede works where supported.

48. Cancel works where supported.

49. Archive works where supported.

50. No DELETE action exists.

51. Permission-aware actions work.

52. Backend `403` is handled.

53. Unknown controls render not found.

54. Cross-tenant controls render the same not-found state.

55. Optimistic concurrency is implemented.

56. Stale writes do not overwrite newer data.

57. `409 Conflict` provides actionable UX.

58. Query keys are stable.

59. Query caches are tenant-safe.

60. Logout clears Risk Control data.

61. Activity uses real backend audit data.

62. Fake client-generated history is not used.

63. User feedback is specific.

64. Desktop layout is production-usable.

65. Tablet and mobile layouts remain usable.

66. Accessibility checks cover major screens.

67. Effectiveness states do not rely on color alone.

68. Storybook contains relevant Risk Control stories.

69. Unit tests pass.

70. Integration/component tests pass.

71. Browser E2E tests pass.

72. Materialization is covered by E2E.

73. Owner assignment is covered by E2E.

74. Implementation flow is covered by E2E.

75. Evidence addition is covered by E2E.

76. Effectiveness verification is covered by E2E.

77. Review scheduling is covered by E2E.

78. Read-only permission scenarios are tested.

79. Cross-tenant behavior is tested.

80. Concurrency conflict behavior is tested.

81. Duplicate materialization is tested.

82. Architecture guardrails pass.

83. Shared UI components are reused.

84. No duplicate general-purpose UI framework is introduced.

85. Strict TypeScript passes.

86. Lint passes.

87. Production build passes.

88. Storybook build passes.

89. Existing authentication tests remain passing.

90. Existing Hazard UI tests remain passing.

91. Existing Risk Assessment UI tests remain passing.

92. Existing backend Risk Control tests remain passing.

93. Correction-record behavior remains deferred.

94. Documentation is complete.

95. The completion report reflects actual implementation and verification results.

---

## Non-Goals

This task does not implement:

- Inspection Management UI;
- Finding Management UI;
- Corrective Action UI;
- Incident Management UI;
- dedicated CorrectionRecord UI;
- binary evidence storage;
- document upload infrastructure;
- Employee Management;
- Competency Management;
- Training Management;
- Knowledge Management;
- organization switching;
- offline mode;
- bulk control management;
- advanced reporting;
- AI-generated controls;
- AI effectiveness verification;
- automatic Risk Assessment changes;
- automatic residual-risk changes;
- frontend-owned compliance decisions;
- new generic workflow engine;
- backend redesign unrelated to concrete UI gaps.

Do not combine Risk Control and Inspection Management into one task.

---

## Verification

### 1. Frontend Installation

Run:

```bash
cd frontend
npm ci
```

Expected:

```text
Installation succeeds without modifying the lock file.
```

---

### 2. Tokens

Run:

```bash
npm run tokens:build
npm run tokens:check
```

Expected:

```text
Generated token outputs are current.
```

---

### 3. Formatting

Run:

```bash
npm run format:check
```

Expected:

```text
No formatting violations.
```

---

### 4. Lint

Run:

```bash
npm run lint
```

Expected:

```text
No lint errors.
```

---

### 5. Type Check

Run:

```bash
npm run typecheck
```

Expected:

```text
No TypeScript errors.
```

Do not suppress errors using broad `any`, unsafe assertions, or disabled compiler rules.

---

### 6. Unit and Integration Tests

Run:

```bash
npm run test
```

Coverage must include:

```text
Risk Control mappers
Status mappings
Effectiveness mappings
Permission capabilities
Query keys
Registry filters
Materialization
Source snapshot
Owner assignment
Implementation planning
Implementation progress
Evidence
Verification
Verification history
Review scheduling
Overdue handling
Lifecycle actions
API errors
Optimistic concurrency
Activity
```

All tests must pass.

---

### 7. Accessibility

Run the configured accessibility tests.

Verify at minimum:

```text
Risk Control Registry
Risk Control Object Page
Owner assignment
Implementation form
Evidence form
Verification form
Review schedule form
Lifecycle confirmation dialogs
Conflict dialog
```

No critical automated accessibility violations are allowed.

---

### 8. Storybook

Run:

```bash
npm run build-storybook
```

Expected:

```text
Storybook build succeeds.
```

Review states in:

```text
Light
Dark
Desktop
Tablet
Mobile
```

---

### 9. Browser E2E

Run:

```bash
npm run test:e2e
```

Required primary workflow:

```text
Login
→ Approved Risk Assessment
→ Materialize Control
→ Risk Control Object Page
→ Assign Owner
→ Plan Implementation
→ Start Implementation
→ Update Progress
→ Add Evidence
→ Complete Implementation
→ Record Verification
→ Schedule Review
→ Verify Final State
```

Required effectiveness cases:

```text
Verified Effective
Verified Partially Effective
Verified Ineffective
```

Required negative scenarios:

```text
Read-only user cannot mutate
User without verify permission cannot verify
Unknown control returns 404
Cross-tenant control returns 404
Stale version displays conflict UX
Duplicate materialization displays conflict UX
Invalid lifecycle action is rejected
Logout clears Risk Control data
```

All tests must pass.

---

### 10. Complete Frontend Verification

Run:

```bash
npm run verify
```

Expected:

```text
tokens
format
lint
typecheck
unit/component tests
production build
```

All checks must pass.

---

### 11. Architecture Guardrails

Run:

```bash
npm run architecture:check
```

or project equivalent.

Verify:

```text
Shared components do not import Risk Control feature code
Feature routes use public APIs
Risk Control API modules do not import presentation components
Presentation components do not call fetch directly
Hazard, Risk Assessment, and Risk Control features do not import each other's internals
Shared UI wrappers are not bypassed
```

---

### 12. Backend Risk Control Tests

Run:

```bash
pytest -m "not db" -k "risk_control"
pytest -m db -k "risk_control"
```

Adapt paths and markers to actual project conventions.

Expected existing hardened baseline includes:

```text
Risk Control non-DB suite passing
Risk Control PostgreSQL contracts passing
Restart persistence passing
Concurrency passing
Materialization passing
Tenant isolation passing
```

All existing backend Risk Control tests must remain passing.

---

### 13. Frontend Regression

Verify that the existing flows remain correct:

```text
Authentication
Hazard Registry
Hazard Object Page
Risk Assessment Registry
Risk Assessment Object Page
Risk Assessment approval
Related Risk Assessments
Related Risk Controls
Permission-aware navigation
Tenant-safe caching
```

---

### 14. Permission Review

Verify with at least:

```text
Risk Control reader
Risk Control implementer
Risk Control verifier
Risk Control reviewer
User without Risk Control access
```

Confirm that each user sees only permitted actions.

Backend authorization remains authoritative.

---

### 15. Tenant Review

Use at least two organizations.

Confirm:

```text
Organization A controls are not listed in Organization B
Organization A control URL returns 404 in Organization B
Materialization cannot cross tenants
Related objects remain tenant-safe
Query cache cannot cross organization boundaries
Logout clears organization-specific Risk Control data
```

---

### 16. Responsive Review

Review:

```text
Mobile
Tablet
Laptop
Desktop
```

Confirm:

- Registry is usable;
- implementation information remains readable;
- evidence remains accessible;
- verification controls remain usable;
- review actions remain reachable;
- Object Page sections stack correctly;
- dialogs fit;
- no unintended horizontal page overflow exists.

---

### 17. Completion Report

Update:

```text
docs/tasks/TASK-P9-007.md
```

Include:

```text
Implementation summary
Frontend routes
Backend endpoints used
Permissions used
Feature structure
Shared components reused
New shared components
Registry capabilities
Materialization workflow
Source snapshot
Owner assignment
Implementation workflow
Evidence
Effectiveness verification
Verification history
Review scheduling
Overdue behavior
Lifecycle actions
Optimistic concurrency
Tenant isolation
Hazard integration
Risk Assessment integration
Activity source
Backend changes
Unit test count
E2E test count
Storybook result
Production build result
Architecture result
CorrectionRecord deferred status
Known limitations
Deferred work
Recommended next task
```

Do not mark the task complete if:

- production APIs are replaced by mock data;
- Risk Assessment materialization is incomplete;
- owner assignment is incomplete;
- implementation workflow is incomplete;
- effectiveness verification is incomplete;
- partial effectiveness is collapsed into another state;
- optimistic concurrency is ignored;
- tenant masking is not verified;
- verification history can be rewritten;
- architecture guardrails fail;
- production build fails;
- Storybook build fails;
- E2E tests fail.

---

## Expected Outcome

SafetyMAIN receives the third complete production-connected frontend business vertical slice.

The user can now execute the complete core risk-management workflow:

```text
Hazard
    ↓
Risk Assessment
    ↓
Proposed Controls
    ↓
Risk Control Materialization
    ↓
Owner Assignment
    ↓
Implementation Planning
    ↓
Implementation
    ↓
Evidence
    ↓
Effectiveness Verification
    ↓
Review
```

The frontend now covers the production backend chain:

```text
Hazard
→ Risk Assessment
→ Risk Control
```

end to end.

The resulting Risk Control UI is:

- authenticated;
- permission-aware;
- tenant-safe;
- lifecycle-oriented;
- implementation-aware;
- evidence-aware;
- verification-aware;
- review-aware;
- concurrency-safe;
- auditable;
- responsive;
- accessible;
- tested end to end;
- built entirely on the approved SafetyMAIN frontend foundation.

After successful completion of this task, SafetyMAIN reaches its first complete frontend **Risk Management MVP**.

The next recommended frontend/business milestone is:

```text
TASK-P9-008 — Inspection Management UI
```

if the Inspection backend is already available.

If Inspection backend development has not yet been completed, proceed first with:

```text
TASK-P8-005 — Inspection Management
```

and then return to the frontend Inspection vertical slice.

---

## Completion Report

Status: **Complete.** Delivered as three sequential sub-tasks —
`TASK-P9-007a` (backend contract patches + read-only slice),
`TASK-P9-007b` (lifecycle & workflow commands), `TASK-P9-007c`
(materialization, guardrails, E2E, documentation) — commit range
`19e9c52..fae1498` on `feature/task-p9-007-risk-control-ui`.

### Implementation summary

The Risk Control feature is the third production-connected frontend
business vertical slice, completing the frontend core risk-management
chain `Hazard → Risk Assessment → Risk Control`. It provides a Risk
Control Registry and Object Page backed entirely by the production
`RiskControl` backend (`TASK-P8-004`/`TASK-P8-004-H1`), a materialization
workflow that turns an approved Risk Assessment's proposed controls into
operational Risk Controls, and the full operational lifecycle: owner
assignment, implementation planning/start/progress/completion, evidence
references, effectiveness verification (Effective / Partially Effective /
Ineffective, kept distinct throughout), review scheduling/completion, and
the five terminal commands (suspend, resume, supersede, cancel, archive —
no delete). Three small backend patches closed concrete gaps the frontend
surfaced (`include_terminal` query param, backend-authoritative
`is_overdue`, `422` instead of `500` for unknown enum query values); no
other backend behavior was changed.

### Frontend routes

```text
/safety/risk-controls               — registry
/safety/risk-controls/[riskControlId] — object page
```

Both are authenticated, gated on `risk_control:read`, and support direct
URL navigation, browser back/forward, and standard not-found rendering for
both unknown and cross-tenant IDs. There is no `/safety/risk-controls/new`
route — controls originate only through Risk Assessment materialization.

### Backend endpoints used

```text
GET    /api/v1/risk-controls
GET    /api/v1/risk-controls/{id}
GET    /api/v1/admin/audit-events?resource_type=RISK_CONTROL&resource_id=
POST   /api/v1/risk-controls/{id}/assign-owner
POST   /api/v1/risk-controls/{id}/plan
POST   /api/v1/risk-controls/{id}/start-implementation
POST   /api/v1/risk-controls/{id}/update-progress
POST   /api/v1/risk-controls/{id}/evidence
POST   /api/v1/risk-controls/{id}/complete-implementation
POST   /api/v1/risk-controls/{id}/verify
POST   /api/v1/risk-controls/{id}/schedule-review
POST   /api/v1/risk-controls/{id}/complete-review
POST   /api/v1/risk-controls/{id}/suspend
POST   /api/v1/risk-controls/{id}/resume
POST   /api/v1/risk-controls/{id}/supersede
POST   /api/v1/risk-controls/{id}/cancel
POST   /api/v1/risk-controls/{id}/archive
POST   /api/v1/risk-assessments/{assessmentId}/materialize-controls
GET    /api/v1/hazards/{id}            (RC-local lite read)
GET    /api/v1/risk-assessments/{id}   (RC-local lite read)
```

`POST /api/v1/risk-controls/materialize` and `POST /api/v1/risk-controls`
(direct creation) exist on the backend but are never called by the
frontend — materialization always goes through the Risk Assessment-scoped
endpoint above. No `DELETE` route is called anywhere; none exists for this
resource by design.

### Permissions used

`risk_control:read` (Registry + Object Page), `risk_control:assign` (owner),
`risk_control:implement` (plan/start/progress/complete implementation,
evidence), `risk_control:verify` (effectiveness verification),
`risk_control:review` (schedule/complete review), `risk_control:suspend`
(both suspend and resume — one backend permission gates both),
`risk_control:supersede`, `risk_control:cancel`, `risk_control:archive`,
`risk_control:materialize` (the materialization dialog). Related reads
piggyback on their owning feature's permission: `hazard:read` (linked
Hazard summary), `risk:read` (linked Risk Assessment summary), `audit:read`
(Activity tab). Capabilities are mapped from the actual permission strings
in `mapRiskControlCapabilities` — never by role name — and every lifecycle
button is additionally gated on the legal transition for the control's
current status, so a capability alone never makes an illegal action appear.

### Feature structure

```text
frontend/src/features/risk-controls/
  api/        transport, TanStack Query, lifecycle command mutations,
              materialization mutation, boundary-safe RA-related-controls
              invalidation
  components/ 18 presentation components incl. MaterializeControlsDialog
  schemas/    RHF + Zod schema per command
  pages/      RiskControlRegistryPage, RiskControlObjectPage
  mappers/    DTO -> view model
  hooks/      permission capabilities, lifecycle action availability,
              command mutation hook
  utils/      status/effectiveness presentation, URL filter state
  types/      transport DTOs + view/capability models
  index.ts    RiskControlRegistryPage, RiskControlObjectPage,
              MaterializeControlsDialog — the only public surface
```

Full structure and rationale: `docs/architecture/frontend/RiskControlManagementUI.md`.

### Shared components reused

`Registry`/`RegistryTable`/`DataTable`, `FilterBar`, `ObjectHeader`,
`ObjectTabs`, `PropertyGrid`/`DescriptionList`, `Panel`/`Card`, `StatusBadge`,
`Timeline`/Activity list, `Dialog`/`ConfirmationDialog`/`WarningDialog`,
`EmptyState`, `Alert`/`Toast`, `Button`, `Checkbox`/`RadioGroup`/`Input`/
form primitives, `NextActionCard`, `BlockingReason` — all imported from
`@/components`, matching the Hazard and Risk Assessment precedent.

### New shared components

**None.** Every UI primitive came from the existing `@/components` Design
System; the feature added zero new entries to the shared component
library. (One shared-component *gap* was found and worked around locally —
see Known limitations in the architecture doc — but not fixed at the
shared-component level, which is out of this task's scope.)

### Registry capabilities

Server-side pagination (offset/limit, default page size 25), backend-fixed
ordering (`created_at DESC, id DESC` — no client sort), and the full
backend filter set wired through URL state: `status`, `hierarchy_level`,
`control_nature`, `hazard_id`, `risk_assessment_id`, `owner_reference`,
`latest_effectiveness_result`, `review_due_before/after`, `overdue_only`,
`awaiting_verification`, `include_terminal` (defaults `false` — terminal
controls hidden unless toggled on), `search`. Distinct loading, first-use
empty, filtered-empty, and error+retry states. Columns: Reference, Control,
Hierarchy Level, Status, Owner, Implementation, Effectiveness, Hazard, Risk
Assessment, Next Review, Overdue, Updated At — all backend-sourced.

### Materialization workflow

`MaterializeControlsDialog`, rendered from the Risk Assessment Object
Page's Related Controls tab through Risk Control's public `index.ts`. Calls
`POST /risk-assessments/{id}/materialize-controls`; enabled unconditionally
from `approved` assessments and behind an explicit checkbox from
`under_review`; lets the user select specific proposed controls or leave
the selection empty for "materialize all eligible"; already-materialized
proposed controls render checked/disabled as a UX affordance (not the
source of truth — the backend still enforces uniqueness); the confirmation
`Alert` states the operation is all-or-nothing; on success, created
control codes are surfaced in a toast and both the Risk Control list
queries and the assessment's related-controls query are invalidated; a
`409` with the `risk_control_already_materialized` code routes to the
duplicate-variant `RiskControlConflictDialog`, distinct from the
stale-version variant. The assessment itself is never mutated client-side.

### Source snapshot behavior

`SourceSnapshot` renders `control.source.snapshot` (source type, source
control reference, assessment version/approved-at, residual level, captured
proposed-control fields) strictly read-only — it never reconstructs the
snapshot from a live fetch of the current Risk Assessment, and shows an
explicit empty state rather than guessing when a control was not
materialized (`snapshot === null`).

### Owner assignment

`ControlOwnerSection` shows the current owner or an empty state, with an
assign/change action gated on `risk_control:assign` and blocked only on the
three terminal-inactive statuses (`superseded`, `archived`, `cancelled`).
Every request carries `expected_version`. No employee/user directory exists
yet — the owner reference is unvalidated free text (documented limitation,
Employee Management is explicitly out of scope for this task).

### Implementation workflow

`ImplementationPlanSection` (plan, `draft` only, once an owner exists:
target dates, method, resource notes, dependencies, evidence/verification
requirements, milestones) plus `ImplementationProgressSection` (start —
`planned → in_implementation`; progress updates — percentage + note,
`in_implementation` only; completion — `in_implementation → implemented`,
required summary, conditional evidence-waiver reason, optional "allow
incomplete milestones"). Completing implementation prompts effectiveness
verification as the next action via `NextActionCard`.

### Evidence behavior

`EvidenceList`/`EvidenceForm` add reference-only evidence records
(external reference, title, description, checksum) — never binary files;
neither component renders a file-upload affordance. Adding evidence after
`implemented` is still legal but requires an explicit "Add evidence after
implementation" acknowledgement checkbox.

### Effectiveness verification

`VerificationForm` offers exactly `effective` / `partially_effective` /
`ineffective` as a `radiogroup` (never `not_verified`/`not_applicable`,
which the backend always rejects here). Display language is "Verified
Effective" / "Verified Partially Effective" / "Verified Ineffective"
throughout — Object Header, Registry, Verification tab, and Activity all
keep Partially Effective visually and textually distinct from both other
outcomes; recording a verification never changes the control's lifecycle
`status`.

### Verification history

Append-only by construction: `VerificationHistory` renders every record
newest-first with the newest tagged "Latest", and no component anywhere
offers edit or delete on a historical record. Dedicated `CorrectionRecord`
support remains deferred to `TASK-P8-HARDENING-001`, per §51 of this
umbrella spec — the frontend does not simulate it.

### Review scheduling

`ReviewScheduleSection` bundles `schedule_review` (frequency and/or
explicit next-review-date, review basis, optional escalation reference, or
a mandatory `noReviewReason` when disabled) and `complete_review` (offered
only once a review is due, optionally bundling a full verification via the
shared verification schema). Two intentional backend quirks are handled
explicitly and covered by dedicated tests: the nested, validated-but-
ignored `expected_version` inside `CompleteReviewRequest.verification`, and
the double version-bump when a verification is included — the frontend
never derives the post-command version itself, it always reads `version`
back from the mapped response.

### Overdue behavior

`control.isOverdue` is read straight from the backend-authoritative
`is_overdue` field (added to `RiskControlResponse` in this task's first
backend patch) and never recomputed client-side; Registry exposes an
`overdue_only` toggle sent straight through as a query parameter.

### Lifecycle actions

`RiskControlLifecycleActions` derives the legal next action(s) from
`availableLifecycleActions`, which mirrors the backend's `_TRANSITIONS`
table as a status→action lookup gated on both the legal transition and the
matching capability. Forward actions (`plan → start_implementation →
complete_implementation → verify → schedule_review`) render first, then the
five terminal commands (`suspend`, `resume`, `supersede`, `cancel`,
`archive`) — none of which is ever presented as, or behaves as, deletion.
No delete action exists anywhere in the feature — verified explicitly by a
dedicated E2E test ("no delete affordance exists on any reachable status").

### Optimistic concurrency

Every mutation, including version-only and reason-only commands, carries
`expected_version`. `RiskControlCommandDialog` surfaces the version being
used in its header. On `409`, the frontend never retries automatically and
never guesses the server's current version — the only recovery path is
`RiskControlConflictDialog`'s "Reload latest," which re-fetches the detail
query. Responses are written into cache directly (never client-computed),
which is what makes the review-completion double version-bump render
correctly without special-casing.

### Tenant isolation

Every query is keyed by `organizationId`. A `404` on detail is rendered
identically whether the control does not exist or belongs to another
organization — the frontend performs no distinguishing check, matching the
backend's masking intent. Related Hazard/Risk Assessment reads only fire
when the corresponding read permission is present and fail silently into
their own section's empty/error state rather than crashing the page.
Logout clears all Risk Control-keyed cache entries through the shared
`AuthProvider` QueryClient reset. Verified directly by the two-organization
E2E scenario ("logout clears data — re-login as a different org shows no
stale rows") and by architecture — no code path bypasses the organization
scoping.

### Hazard integration

The Object Page's Overview tab and header display the linked Hazard via a
lite read (`GET /api/v1/hazards/{id}`), gated on `hazard:read`, navigating
through Hazard's public route. Risk Control imports no Hazard internals;
Hazard imports no Risk Control internals (both directions enforced by
dependency-cruiser).

### Risk Assessment integration

Two integration points, both one-directional through public feature
boundaries: (1) the Object Page displays the linked Risk Assessment and its
immutable source snapshot via a lite read, gated on `risk:read`; (2) the
Risk Assessment Object Page renders Risk Control's `MaterializeControlsDialog`
(imported only via `@/features/risk-controls`) inside its Related Controls
tab. Neither feature imports the other's internal types, mappers,
mutations, or query keys — see `RiskAssessmentManagementUI.md`'s "Related
controls and materialization" section for the Risk Assessment side.

### Activity source

`RiskControlActivity` reads exclusively from
`GET /api/v1/admin/audit-events?resource_type=RISK_CONTROL&resource_id=`,
gated on `audit:read`. `ACTIVITY_TITLES` maps the `safety.risk_control.*`
audit taxonomy to human-readable titles, falling back to the raw event name
for anything unmapped. No fake or client-synthesized history is ever
rendered — the Activity tab itself only renders when the permission is
present.

### Backend changes

Three focused patches, each with dedicated tests, all preserving
TenantContext/RBAC/audit/optimistic-concurrency/cross-tenant masking/
migration compatibility:

1. `19e9c52` — `feat(api): expose include_terminal on risk control registry
   endpoint` (`backend/api/routers/risk_controls.py`). The parameter
   already flowed through the query and both repositories but was never
   exposed over HTTP, so the registry always hid superseded/archived/
   cancelled controls. Test: `test_list_risk_controls_include_terminal_
   exposes_archived`.
2. `8059722` — `feat(api): expose backend-authoritative is_overdue on risk
   control responses` (`backend/api/mappers/risk_controls.py`,
   `backend/api/schemas/risk_controls.py`). Test:
   `test_risk_control_response_exposes_is_overdue`.
3. `68efdbf` — `fix(api): return 422 for unknown risk control enum query
   params` (`backend/api/routers/risk_controls.py`). Previously an unknown
   enum value in a list filter (e.g. `status=bogus`) fell through to an
   unhandled `500`; `_parse_enum_param` now maps it to a `422` with an
   explicit `allowed values` message. Tests:
   `test_list_risk_controls_rejects_unknown_enum_param[status]`,
   `[hierarchy_level]`, `[control_nature]`, `[latest_effectiveness_result]`.

During this completion pass, `_parse_enum_param`'s `TypeVar`-based generic
was additionally converted to PEP 695 syntax (`def _parse_enum_param[EnumT:
Enum](...)`) to clear a `ruff` `UP047` finding introduced by that same
function — a one-line style fix, not a behavior change; covered by the
existing tests above (all still pass).

### Unit test count

**259 frontend unit/component tests pass** across 24 test files
(`npm run test` / Vitest), of which **171 are Risk Control-specific**:
`risk-control-mappers.test.ts` (11), `risk-control-status.test.ts` (6),
`risk-control-permissions.test.ts` (15), `risk-control-query-keys.test.ts`
(4), `risk-control-filters.test.ts` (12), `risk-control-commands.test.ts`
(9), `risk-control-command.test.tsx` (4), `risk-control-command-hook.
test.tsx` (10), `materialization.test.tsx` (7), and `risk-control-
workflow.test.tsx` (93, covering every Phase B component plus an
axe-core accessibility pass). The remaining 88 tests cover the
pre-existing Hazard, Risk Assessment, auth, and shared-component suites
and all remain green — no regression.

### E2E test count

**34 Playwright tests pass** (`npm run test:e2e`), of which **20 are Risk
Control-specific** (`e2e/risk-controls.spec.ts`: 1 main-workflow, 3
effectiveness-result, 11 negative-scenario, 4 terminal-command). The
remaining 14 are the pre-existing `auth.spec.ts` (4), `hazards.spec.ts`
(4), `risk-assessments.spec.ts` (5), and `smoke.spec.ts` (1) — all pass
unchanged, confirming no regression in authentication, Hazard, or Risk
Assessment E2E coverage.

### Storybook result

`npm run build-storybook` **succeeds**. `risk-controls.stories.tsx` covers
`RiskControlSummary`, `ControlOwnerSection`, `ImplementationPlanSection`,
`ImplementationProgressSection`, `EvidenceList`, `EffectivenessSummary`,
`VerificationHistory`, `VerificationForm`, `ReviewScheduleSection`,
`SourceSnapshot`, and `RiskControlLifecycleActions` across their key
states (default/loading/empty/read-only/unassigned/planned/in-progress/
implemented/Effective/Partially Effective/Ineffective/overdue/archived/
permission-limited/dark theme/narrow viewport) with deterministic fixtures.

### Production build result

`next build` **succeeds**. Both new routes compile and prerender/render
correctly: `/safety/risk-controls` (static, 253 kB First Load JS) and
`/safety/risk-controls/[riskControlId]` (dynamic, 253 kB First Load JS).

### Architecture result

`npm run architecture:check` **passes** — 0 dependency violations across
349 modules / 1,247 dependencies. Two Risk-Control-specific dependency-
cruiser rules were added in this sub-task (`risk-control-api-no-
components`, `risk-control-presentation-no-fetch`), alongside the
pre-existing cross-feature boundary rules, which continue to hold for
`risk-controls` unchanged.

### CorrectionRecord deferred status

Confirmed deferred, unchanged from the umbrella spec's Outcome A. The
frontend renders all verification history as read-only and append-only,
offers no edit/delete affordance on any historical record, and does not
simulate correction-record behavior anywhere. Tracked for a future task:
`TASK-P8-HARDENING-001 — Historical Correction Records`.

### Known limitations

- No employee/user directory — owner assignment and any reviewer/verifier
  references use raw, backend-unvalidated free text.
- `409` responses do not carry the server's current version; recovery is
  always a re-GET through the conflict dialog's "Reload latest," never an
  inferred merge.
- `competency_requirements` and `related_entities` are read-only over HTTP
  and always empty in the current backend — displayed but not editable.
- Suspension/cancel/archive/supersede reasons are only visible via the
  audit API (`audit:read`), not on the Risk Control response itself.
- The shared `components/dialogs/*` primitives (`Dialog`,
  `ConfirmationDialog`, `WarningDialog`) restore focus to `Dialog.Trigger`
  by default, which is `null` for every dialog in this feature (all are
  opened from a plain `Button` against externally-held `open` state).
  `RiskControlCommandDialog`, `RiskControlConflictDialog`, and
  `MaterializeControlsDialog` all work around this locally; the shared
  primitive itself was not changed (see Deferred work).
- The "already materialized" checkbox state in the materialization dialog
  is a client-side UX affordance derived from a fetch at dialog-open time,
  not authoritative — a concurrent materialization between that fetch and
  submit still surfaces as a `409` handled by the standard conflict path.

### Deferred work

Per §52 of this specification, explicitly deferred: dedicated
`CorrectionRecord` UI (→ `TASK-P8-HARDENING-001`), binary evidence upload,
document management, Inspection UI, Finding UI, Corrective Action UI,
Incident UI, Employee Management UI, Competency Management UI, Training UI,
Knowledge UI, organization switching, offline mode, bulk Risk Control
editing, bulk evidence upload, saved registry views backed by persistence,
advanced analytics, AI control recommendations, AI verification decisions,
automatic residual-risk mutation, real-time collaborative editing,
websocket updates. Additionally deferred as a carry-over from Phase B: the
shared `components/dialogs/*` focus-restore fix (see Known limitations).

### Recommended next task

The Inspection domain has only a bare entity (`backend/core/domain/
entities/inspection.py`) and repository interface (`backend/core/domain/
repositories/inspection_repository.py`) — no application handlers, no
persistence, and no API router wired into `backend/api/app.py` or
`backend/bootstrap/container.py`. The Inspection backend is therefore
**not yet production-usable**. Recommended next task:

```text
TASK-P8-005 — Inspection Management
```

(backend: aggregate, handlers, persistence, REST API), followed by the
frontend Inspection Management UI vertical slice once that backend is
complete.

### Verification summary (actual numbers, this pass)

```text
Frontend
  npm run verify              PASS  (tokens, format, lint, typecheck,
                                      architecture:check, 259 tests / 24
                                      files, production build)
  npm run architecture:check  PASS  (0 violations, 349 modules, 1247 deps)
  npm run build-storybook     PASS
  npm run test:e2e            PASS  (34/34, incl. 20 risk-controls)

Backend
  pytest -k risk_control -v          35 passed, 11 skipped (DB-marked)
  pytest (full suite, no DB)         788 passed, 133 skipped
  pytest -m db -k risk_control       11 passed (against real PostgreSQL 17,
                                      after `alembic upgrade head`)
  ruff check .                       367 pre-existing findings, unrelated
                                      to this plan (verified identical at
                                      commit 03817cc, before TASK-P9-007
                                      began, via a disposable git worktree);
                                      one additional finding introduced by
                                      this plan's own new code (UP047 in
                                      backend/api/routers/risk_controls.py)
                                      was fixed during this pass, restoring
                                      the count to the 367 baseline
```

All gates pass. No test was skipped to reach a green result other than the
pre-existing, environment-gated `-m db` skip semantics (resolved here by
starting Postgres via `docker compose up -d` and running with
`SAFETYMAIN_RUN_DB_TESTS=1` and a `postgresql+psycopg://` URL matching the
installed `psycopg[binary]` v3 driver — the brief's example URL uses the
bare `postgresql://` scheme, which SQLAlchemy resolves to the psycopg2
driver by default; that driver is not installed in this environment, only
`psycopg[binary]` per `pyproject.toml`, so the `+psycopg` scheme is
required here).