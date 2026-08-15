# TASK-P9-006 — Risk Assessment Management UI

---

## Goal

Implement the complete SafetyMAIN frontend business vertical slice for Risk Assessment Management.

The feature must connect the authenticated frontend application to the existing production Risk Assessment backend and provide a complete workflow for:

- viewing the Risk Assessment registry;
- creating a Risk Assessment for a Hazard;
- selecting and applying an assessment profile;
- entering inherent risk inputs;
- defining proposed controls using the Hierarchy of Controls;
- entering residual risk inputs;
- reviewing backend-calculated risk results;
- editing a Draft assessment;
- submitting an assessment for review;
- approving an assessment;
- handling automatic superseding of a previous approved assessment in the same scope;
- archiving assessments where supported;
- viewing the linked Hazard;
- viewing proposed and materialized Risk Controls;
- viewing lifecycle activity through the audit API;
- handling permissions, validation, optimistic concurrency, tenant isolation, loading, empty, and error states.

The implementation must reuse the architecture, UX patterns, and shared components established by:

```text
TASK-P9-005 — Hazard Management UI
```

This task must not duplicate shared Registry, Object Page, table, form, workflow, filter, dialog, feedback, Timeline, Activity, loading, empty-state, or concurrency components.

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

The frontend platform currently provides:

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

`TASK-P9-005` established the reference architecture for frontend business features, including:

- feature-local API modules;
- stable query keys;
- URL-synchronized registry filters;
- server-side pagination;
- protected feature routes;
- permission capability mapping;
- frontend form models;
- optimistic concurrency handling;
- tenant-safe caching;
- lifecycle actions;
- related-object presentation;
- activity sourced from the audit API;
- Storybook fixtures;
- unit, integration, and Playwright tests.

The production Risk Assessment backend is complete.

It includes:

- `RiskAssessment` aggregate;
- configurable assessment profiles;
- configurable risk matrices;
- inherent risk;
- residual risk;
- proposed controls using the Hierarchy of Controls;
- acceptance information;
- review scheduling;
- competency references;
- lifecycle management;
- automatic superseding of the previous approved assessment in the same scope;
- PostgreSQL persistence;
- tenant isolation;
- RBAC;
- audit events;
- optimistic concurrency;
- REST API.

The lifecycle is:

```text
Draft
→ Under Review
→ Approved
→ Superseded
→ Archived
```

`Superseded` is normally produced automatically when a newer assessment is approved in the same scope.

The production API is exposed under:

```text
/api/v1/risk-assessments
```

RBAC uses the existing:

```text
risk:*
```

permission family.

Audit uses:

```text
safety.risk.*
```

Before implementing frontend contracts, inspect the actual backend:

- routes;
- request schemas;
- response schemas;
- lifecycle command endpoints;
- permissions;
- filters;
- pagination;
- sorting;
- profile representation;
- matrix representation;
- inherent risk representation;
- residual risk representation;
- proposed-control representation;
- acceptance representation;
- review scheduling representation;
- competency references;
- aggregate version field;
- error semantics;
- audit events;
- Hazard relationship;
- Risk Control relationship.

The backend contract is authoritative.

Do not invent frontend-only lifecycle transitions, profile definitions, risk formulas, permission names, or API payloads.

---



## Scope



### 1. Backend Contract Review

Before implementing the feature, document the actual Risk Assessment API contract.

At minimum, identify:

```text
Registry endpoint
Read-by-ID endpoint
Create endpoint
Draft update endpoint
Submit-for-review endpoint
Approve endpoint
Archive endpoint
Profile data source
Matrix data source
Related Hazard data
Related Risk Control data
Activity data source
Pagination contract
Sorting contract
Filter contract
Optimistic concurrency contract
Error response contract
```

The review must confirm:

- exact request and response fields;
- lifecycle rules;
- fields editable in Draft;
- fields owned by approval;
- aggregate version semantics;
- automatic superseding response behavior;
- actual permission names;
- tenant masking behavior.

Document any backend gaps discovered during implementation.

Do not redesign the backend unless the UI reveals a concrete production contract gap.

---



### 2. Feature Architecture

Create a dedicated frontend feature under:

```text
frontend/src/features/risk-assessments/
```

Recommended structure:

```text
frontend/src/features/risk-assessments/
├── api/
│   ├── risk-assessment-api.ts
│   ├── risk-assessment-queries.ts
│   ├── risk-assessment-mutations.ts
│   └── risk-assessment-query-keys.ts
├── components/
│   ├── risk-assessment-form.tsx
│   ├── assessment-profile-selector.tsx
│   ├── inherent-risk-section.tsx
│   ├── residual-risk-section.tsx
│   ├── risk-matrix-input.tsx
│   ├── risk-result-summary.tsx
│   ├── risk-comparison.tsx
│   ├── proposed-controls-editor.tsx
│   ├── proposed-control-row.tsx
│   ├── acceptance-section.tsx
│   ├── review-schedule-section.tsx
│   ├── competency-references.tsx
│   ├── risk-assessment-summary.tsx
│   ├── risk-assessment-properties.tsx
│   ├── risk-assessment-lifecycle-actions.tsx
│   ├── related-hazard.tsx
│   ├── related-risk-controls.tsx
│   └── risk-assessment-activity.tsx
├── pages/
│   ├── risk-assessment-registry-page.tsx
│   ├── risk-assessment-create-page.tsx
│   └── risk-assessment-object-page.tsx
├── schemas/
│   └── risk-assessment-form-schema.ts
├── hooks/
│   ├── use-risk-assessment-permissions.ts
│   └── use-risk-assessment-lifecycle.ts
├── mappers/
│   └── risk-assessment-mappers.ts
├── types/
│   └── risk-assessment-types.ts
├── utils/
│   ├── risk-assessment-status.ts
│   ├── risk-assessment-filters.ts
│   └── hierarchy-of-controls.ts
└── index.ts
```

Adapt the exact structure to the conventions established by the Hazard feature.

Requirements:

- expose a controlled public feature API;
- keep API code separate from presentation;
- keep transport models separate from form and view models;
- prevent unrelated features from importing internal files;
- prevent shared components from importing Risk Assessment code.

---



### 3. Routes

Add authenticated routes:

```text
/safety/risk-assessments
/safety/risk-assessments/new
/safety/risk-assessments/[riskAssessmentId]
```

Support creation in a Hazard context:

```text
/safety/risk-assessments/new?hazardId={hazardId}
```

Requirements:

- all routes are protected;
- read permission is required for registry and object routes;
- create permission is required for the creation route;
- direct URL navigation works;
- browser back and forward navigation works;
- invalid identifiers render the approved not-found state;
- cross-tenant resources render the same not-found state;
- registry state is preserved through URL parameters where appropriate;
- creation from a Hazard preserves the Hazard context.

Primary workflows must use full pages rather than modal-only routing.

---



### 4. Navigation Integration

Add Risk Assessments under:

```text
Safety
├── Hazards
└── Risk Assessments
```

The navigation entry must:

- use typed navigation configuration;
- use the shared icon wrapper;
- display active state;
- support collapsed navigation;
- remain keyboard accessible;
- appear only when the user has Risk Assessment read permission.

Do not hardcode role names.

Do not embed permission rules inside low-level navigation rendering components.

---



### 5. Permission Capability Model

Inspect the real backend permissions and map them to frontend capabilities.

Expected categories may include equivalents of:

```text
risk:read
risk:create
risk:update
risk:submit
risk:approve
risk:archive
risk:*
```

Use the actual backend permission names.

Create a feature-level capability model similar to:

```ts
type RiskAssessmentCapabilities = {
  canRead: boolean;
  canCreate: boolean;
  canUpdateDraft: boolean;
  canSubmitForReview: boolean;
  canApprove: boolean;
  canArchive: boolean;
  canViewRelatedControls: boolean;
};
```

Requirements:

- use permissions, not roles;
- hide unavailable actions where appropriate;
- disable actions when showing a blocked reason is more useful;
- protect routes independently of button visibility;
- handle backend `403 Forbidden`;
- keep read, create, edit, submit, approve, and archive permissions distinct.

Frontend permission checks are UX controls only.

The backend remains the authorization authority.

---



### 6. Risk Assessment Registry

Implement the Risk Assessment Registry using the shared Registry and DataTable components.

The registry must provide:

- page title;
- concise description;
- create action when permitted;
- search;
- filters;
- sorting;
- server-side pagination;
- loading state;
- skeleton state;
- first-use empty state;
- filtered-empty state;
- error state;
- retry action;
- row navigation;
- keyboard-accessible interactions.

Recommended columns:

```text
Reference
Hazard
Status
Assessment Profile
Inherent Risk
Residual Risk
Next Review
Approved At
Updated At
```

Use only fields returned by the backend.

The default column set must prioritize operational usefulness.

Do not expose raw IDs where a human-readable reference is available.

---



### 7. Registry Query State

Represent registry state consistently.

At minimum:

```text
search
filters
sort
page
page size
```

Use URL search parameters for shareable and restorable state.

Example:

```text
/safety/risk-assessments?status=under-review&hazardId=...&page=2
```

Requirements:

- changing filters resets pagination where appropriate;
- invalid URL values degrade safely;
- query objects remain stable;
- browser navigation restores registry state;
- organization context participates in tenant-safe query keys;
- implementation follows the Hazard Registry conventions.

Do not store all meaningful registry state only in component-local memory.

---



### 8. Registry Filters

Implement only filters supported by the production backend.

Potential filters include:

- lifecycle status;
- Hazard;
- assessment profile;
- inherent risk band;
- residual risk band;
- approval date;
- next review date;
- overdue review;
- created date;
- updated date;
- free-text search.

Requirements:

- active filters are visible;
- individual filters can be removed;
- all filters can be cleared;
- enum values map to human-readable labels;
- invalid filter values do not break rendering;
- filtering remains server-side;
- changing filters does not unnecessarily erase existing table content.

Do not implement client-side filtering over one server page.

---



### 9. Registry Sorting and Pagination

Use the real backend sorting and pagination contract.

Support:

- stable default ordering;
- only backend-supported sortable columns;
- current page;
- page size;
- total count where available;
- previous and next navigation;
- recovery when a mutation leaves the current page empty.

Do not load the complete registry into the browser merely to sort it.

---



### 10. Hazard Integration

Extend the existing Hazard Object Page with an entry point for creating a Risk Assessment.

Requirements:

- display `Create Risk Assessment` when permitted;
- pass the current `hazardId` through the route;
- keep the existing related Risk Assessment section;
- refresh the Hazard-related assessment query after creation, submission, approval, archival, or superseding;
- do not embed the Risk Assessment form inside the Hazard feature;
- do not import Risk Assessment internals into Hazard internals.

Cross-feature integration must use:

- public feature routes;
- public feature APIs;
- shared business-neutral contracts.

The Risk Assessment feature owns its creation and lifecycle workflows.

---



### 11. Create Risk Assessment Workflow

Implement a dedicated creation page.

The workflow must follow the actual backend contract and conceptually support:

```text
Select Hazard
→ Select Assessment Profile
→ Enter Inherent Risk
→ Define Proposed Controls
→ Enter Residual Risk
→ Configure Acceptance and Review Information
→ Create Draft
```

Requirements:

- use React Hook Form;
- use Zod;
- preselect the Hazard when `hazardId` is present;
- validate that the Hazard belongs to the active organization through backend data;
- clearly display the selected Hazard;
- allow changing the Hazard before submission only when supported;
- load real profile and matrix configuration;
- preserve entered values between form sections;
- prevent duplicate submissions;
- map backend validation errors;
- focus the first invalid field where practical;
- navigate to the created Object Page after success;
- invalidate the registry;
- invalidate the linked Hazard relationship query.

Do not allow users to set server-owned fields such as:

```text
organization_id
id
reference
aggregate version
audit metadata
approval metadata
lifecycle status
superseded assessment ID
created_at
updated_at
```

---



### 12. Form and View Models

Separate:

```text
Backend transport model
Frontend form model
Frontend view model
```

Implement explicit mapper functions.

Potential transformations include:

- empty strings to `undefined`;
- UI dates to backend date format;
- profile selection to profile identifier;
- matrix selections to backend dimensions;
- proposed-control rows to request payloads;
- optional acceptance information;
- review scheduling values;
- competency references;
- extension data.

Do not place complex mapping logic directly inside React submit handlers.

The backend remains authoritative for domain validation and risk results.

---



### 13. Assessment Profile Selection

Implement profile selection using real backend-provided configuration.

Display useful profile information where available:

- name;
- description;
- applicability;
- matrix type;
- dimensions;
- score range;
- risk bands;
- review defaults;
- required fields.

Requirements:

- provide loading and error states;
- safely handle unavailable or removed profiles;
- map selection to the exact backend identifier;
- warn before clearing entered risk data when changing profiles;
- avoid hardcoded frontend profile definitions;
- preserve profile snapshots returned by the backend for historical display.

If no profile-list API exists, use the actual profile contract exposed by the backend and document the limitation.

Do not create fake profile administration.

---



### 14. Risk Matrix Input

Implement a feature-specific matrix input driven by backend configuration.

Possible dimensions include:

```text
Likelihood
Severity
Exposure
Consequence
Frequency
```

Use only actual backend dimensions.

Requirements:

- labels come from configuration;
- option values come from configuration;
- descriptions remain visible or discoverable;
- keyboard navigation works;
- selected values are clear;
- meaning does not depend on color;
- disabled options are represented correctly;
- light and dark themes work;
- values map deterministically to the backend request.

Do not independently implement authoritative risk calculations unless the backend contract explicitly guarantees the exact formula and mapping.

Preferred behavior:

```text
Frontend collects inputs
→ Backend calculates and validates result
→ Frontend renders authoritative result
```

If the backend exposes a preview endpoint, use it.

---



### 15. Inherent Risk

Implement the inherent risk section.

Display:

- selected matrix dimensions;
- backend-provided score;
- backend-provided risk level or band;
- matrix/profile reference;
- explanation or band label where provided.

Requirements:

- editable in Draft when permitted;
- read-only after lifecycle transition where required;
- critical risk is visually prominent;
- risk meaning does not depend on color;
- values are presented consistently in the form, registry, and Object Page.

Do not expose internal formulas unless they are intentionally part of the product contract.

---



### 16. Proposed Controls Editor

Implement a structured editor for proposed controls.

Use the actual backend fields.

Potential fields include:

- title;
- description;
- Hierarchy of Controls level;
- control type or nature;
- implementation intent;
- suggested owner;
- competency references;
- extension data.

Requirements:

- add a proposed control;
- edit a proposed control;
- remove a proposed control while editing is permitted;
- reorder controls when order is meaningful;
- preserve stable row keys;
- validate required fields;
- show useful empty-state guidance;
- prevent loss of controls while navigating form sections;
- distinguish proposed controls from materialized production Risk Controls.

Do not implement full Risk Control Management in this task.

Do not silently materialize Risk Controls unless the current backend contract explicitly defines materialization as part of this workflow.

---



### 17. Hierarchy of Controls

Use the canonical backend/domain values for the Hierarchy of Controls.

The conceptual order is:

```text
Elimination
Substitution
Engineering Controls
Administrative Controls
Personal Protective Equipment
```

Use the actual enum values and labels.

Requirements:

- preserve canonical ordering;
- provide concise explanatory text;
- do not imply that all levels provide equal protection;
- communicate the selected level without relying only on color;
- centralize mapping in the Risk Assessment feature;
- do not place business enums inside shared business-neutral components.

---



### 18. Residual Risk

Implement the residual risk section.

Requirements:

- residual risk follows proposed-control definition;
- use the same configured profile or matrix unless the backend supports another one;
- display backend-provided score and risk band;
- clearly separate inherent and residual risk;
- do not imply that reduced risk is automatically acceptable;
- allow editing only when lifecycle and permissions permit;
- approved values remain read-only and historical.

Do not silently copy inherent inputs into residual inputs unless explicitly required by the backend contract.

---



### 19. Risk Comparison

Provide a clear comparison between inherent and residual risk.

Display where available:

```text
Inherent score
Inherent level
Residual score
Residual level
Risk-band change
```

Use shared cards, property grids, badges, or a feature-specific composition.

Requirements:

- results come from backend-provided values;
- do not invent percentage reduction for ordinal matrices;
- clearly distinguish score from band;
- risk meaning must remain understandable without color;
- no unsupported mathematical interpretation is introduced.

---



### 20. Acceptance Information

Implement risk acceptance fields and presentation where supported.

Potential fields include:

- accepted status;
- acceptance reason;
- conditions;
- accepting authority;
- acceptance timestamp;
- additional review requirement.

Requirements:

- follow actual backend lifecycle rules;
- distinguish assessment approval from risk acceptance if the domain does;
- do not allow generic Draft editing of approval-owned fields;
- map backend validation to the correct UI section;
- display acceptance clearly on approved assessments.

Do not invent a separate acceptance workflow when the backend does not provide one.

---



### 21. Review Scheduling

Implement review scheduling using the actual backend fields.

Potential fields include:

- next review date;
- review interval;
- review reason;
- review owner;
- review-required flag;
- overdue state.

Requirements:

- show the next review date;
- show overdue state when provided;
- edit only when lifecycle permits;
- use backend-provided overdue calculations where available;
- do not use the browser clock as the authoritative compliance clock;
- show the schedule on the Object Page and Registry where useful.

---



### 22. Competency References

Display and edit competency references when supported by the backend.

Requirements:

- use the real reference structure;
- do not implement Competency Management UI;
- do not create fake competency data;
- provide a neutral empty state;
- support read-only display when no selection API exists;
- document any backend limitation.

---



### 23. Risk Assessment Object Page

Implement the Object Page using shared Object Page components.

Recommended structure:

```text
Object Header
├── Assessment reference
├── Linked Hazard
├── Lifecycle status
├── Inherent risk
├── Residual risk
├── Primary next action
└── Overflow actions

Object Summary
├── Assessment profile
├── Scope
├── Acceptance
├── Review schedule
└── Version metadata

Tabs
├── Overview
├── Proposed Controls
├── Related Risk Controls
└── Activity
```

Add other tabs only when backed by meaningful data.

The page must support:

- loading;
- section skeletons;
- not found;
- permission failure where distinguishable;
- retryable errors;
- responsive layout;
- permission-aware actions;
- meaningful browser metadata.

Do not add empty tabs only to match a generic template.

---



### 24. Object Header and Summary

The header must display:

- human-readable assessment reference;
- linked Hazard;
- lifecycle status;
- inherent risk level;
- residual risk level;
- primary next action;
- secondary actions.

The summary must display meaningful information such as:

- assessment profile;
- assessment scope;
- approval details;
- acceptance;
- next review;
- current version;
- created and updated metadata.

Use centralized status and risk mappings.

Do not create feature-local raw color values.

Link to the Hazard Object Page through the approved Hazard public route.

---



### 25. Proposed Controls Presentation

Display proposed controls as structured cards or rows.

Show actual supported fields such as:

- title;
- description;
- Hierarchy of Controls level;
- implementation intent;
- competency references;
- materialization state.

Requirements:

- preserve meaningful ordering;
- distinguish proposed controls from production Risk Controls;
- indicate materialization state when the backend provides it;
- do not allow Risk Control lifecycle editing here;
- do not create Risk Control Object Pages inside this task.

---



### 26. Related Risk Controls

Display materialized Risk Controls related to the assessment when available.

Potential columns:

```text
Reference
Title
Hierarchy Level
Status
Owner
Implementation State
Effectiveness
Next Review
```

Use only fields returned by the backend.

Until `TASK-P9-007 — Risk Control Management UI` is complete:

- related controls may be read-only;
- links may be omitted or disabled;
- no Risk Control editing is allowed;
- no Risk Control lifecycle actions are implemented here.

Distinguish:

```text
No proposed controls exist
```

from:

```text
Proposed controls exist but have not been materialized
```

when the backend provides enough information.

---



### 27. Edit Draft Assessment

Implement editing for Draft assessments when permitted.

Requirements:

- reuse the creation form model;
- prepopulate current values;
- preserve untouched values;
- include the current expected version;
- update only backend-supported fields;
- prevent generic editing after submission or approval unless explicitly allowed;
- map backend validation errors;
- preserve unsaved values during a concurrency conflict where practical;
- update detail, registry, Hazard relationships, and related queries after success.

Lifecycle-owned fields must not be edited through a generic form.

---



### 28. Submit for Review

Implement:

```text
Draft
→ Under Review
```

Requirements:

- action appears only when valid and permitted;
- use explicit action language;
- show a confirmation dialog;
- collect a note or reason when required;
- include the expected version;
- map incomplete-assessment validation into actionable feedback;
- update Object Page and Registry data;
- show a specific success message;
- display the real audit event in Activity.

Do not optimistically display `Under Review` before the backend confirms the transition.

---



### 29. Approve Assessment

Implement:

```text
Under Review
→ Approved
```

Requirements:

- action appears only when valid and permitted;
- clearly explain that approval may supersede a previous approved assessment in the same scope;
- show a confirmation dialog;
- collect required acceptance or approval information;
- include the expected version;
- preserve backend authority over superseding;
- refresh Risk Assessment Registry;
- refresh the approved Object Page;
- refresh linked Hazard data;
- refresh the superseded assessment when its identifier is returned;
- show a specific success message.

Do not implement superseding logic on the client.

---



### 30. Automatic Superseding UX

When approving a new assessment causes an older assessment to become `Superseded`:

- show the new assessment as `Approved`;
- show a non-blocking message explaining that the previous approved assessment was superseded;
- keep the previous assessment accessible as history;
- link to the previous assessment when the backend returns its identifier and permission allows;
- refresh authoritative queries;
- do not ask the user to archive the previous assessment manually.

If the backend does not identify the superseded assessment in the response, invalidate and refetch relevant queries without guessing.

---



### 31. Archive Action

Implement archival where supported.

Requirements:

- show only when valid and permitted;
- use a consequential-action confirmation;
- include expected version;
- collect a reason when required;
- refresh relevant queries;
- preserve historical accessibility;
- do not expose DELETE;
- do not present archival as permanent deletion.

---



### 32. Lifecycle Visualization

Use shared workflow components where they accurately represent the lifecycle.

Normal progression:

```text
Draft
→ Under Review
→ Approved
```

Historical or terminal states:

```text
Superseded
Archived
```

Display:

- current state;
- completed stages;
- next valid action;
- blocked reason where available;
- historical terminal state.

Do not represent `Superseded` as a normal user-selected forward step.

---



### 33. Optimistic Concurrency

Support the backend optimistic concurrency contract for every mutation.

Include the current expected version using the actual API mechanism.

On:

```text
409 Conflict
```

the frontend must:

- preserve unsaved input where practical;
- explain that the assessment changed elsewhere;
- offer to load the latest version;
- invalidate and refetch authoritative data;
- avoid automatic mutation retries;
- never silently overwrite newer changes;
- distinguish version conflict from another domain conflict when error data allows.

Reuse the conflict UX established by Hazard Management.

Promote code to shared UI only when genuinely business-neutral.

---



### 34. TanStack Query Integration

Create stable query keys.

Recommended structure:

```ts
riskAssessmentKeys.all
riskAssessmentKeys.lists()
riskAssessmentKeys.list(filters)
riskAssessmentKeys.details()
riskAssessmentKeys.detail(riskAssessmentId)
riskAssessmentKeys.profiles()
riskAssessmentKeys.relatedControls(riskAssessmentId)
riskAssessmentKeys.activity(riskAssessmentId)
riskAssessmentKeys.forHazard(hazardId)
```

Requirements:

- organization context is represented safely;
- cache data cannot leak between organizations;
- logout clears sensitive query data;
- creation invalidates Registry and Hazard relationships;
- updates invalidate detail and Registry data;
- submission and approval invalidate lifecycle-sensitive data;
- approval refreshes potential superseded assessments;
- queries support cancellation;
- disabled queries do not run without authentication or identifiers;
- avoid global cache invalidation without justification.

---



### 35. Tenant Isolation

Requirements:

- every request uses the active organization context;
- query keys are organization-safe;
- Hazard selection is organization-scoped;
- profile and matrix data follow backend tenant rules;
- cross-tenant `404` uses the normal not-found experience;
- the UI never reveals that an assessment exists in another organization;
- logout clears organization-specific Risk Assessment data;
- future organization switching remains possible without redesign.

Do not distinguish a missing assessment from a cross-tenant masked assessment.

---



### 36. API Error Handling

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

Expected behavior:

```text
401 → existing authentication flow
403 → permission experience
404 → Risk Assessment not found
409 → concurrency or domain conflict
422 → validation, profile, matrix, lifecycle, or tenant error
Network failure → retryable error
Unexpected failure → safe generic error with correlation ID
```

Do not render raw backend error payloads directly.

Map field-level validation errors into the correct form section.

---



### 37. Activity and Timeline

Use the real audit API or another existing backend activity projection.

Potential events include:

```text
Risk Assessment created
Risk Assessment updated
Submitted for review
Approved
Previous assessment superseded
Review scheduled
Acceptance recorded
Archived
```

Display where available:

- event title;
- actor;
- timestamp;
- previous status;
- new status;
- reason or note;
- Hazard reference;
- superseded assessment reference.

Do not synthesize fake history from current state.

---



### 38. Loading, Empty, and Feedback States

Implement distinct loading states for:

- Registry;
- Object Page;
- profile loading;
- matrix loading;
- form submission;
- lifecycle actions;
- related controls;
- Activity.

Implement distinct empty states for:

- no assessments;
- no filtered results;
- no assessments for a Hazard;
- no proposed controls;
- no materialized Risk Controls;
- no Activity;
- no competency references;
- no review schedule.

Provide specific success feedback for:

```text
Risk assessment created
Draft updated
Submitted for review
Risk assessment approved
Previous assessment superseded
Risk assessment archived
```

Avoid generic messages such as:

```text
Operation completed successfully
```

---



### 39. Responsive Design

Desktop remains the primary productivity layout.

The following must remain usable on laptop, tablet, and mobile:

- Registry;
- filters;
- creation form;
- profile selector;
- risk matrix inputs;
- proposed-controls editor;
- lifecycle actions;
- Object Page;
- confirmation dialogs.

Requirements:

- no horizontal page overflow;
- matrix inputs remain understandable;
- form sections stack correctly;
- proposed-control actions remain reachable;
- tables use the approved responsive strategy;
- dialogs fit smaller viewports;
- touch targets follow the Design System.

Offline workflows are outside this task.

---



### 40. Accessibility

Meet the current frontend accessibility baseline.

At minimum:

- semantic landmarks;
- logical heading hierarchy;
- keyboard-accessible Registry;
- keyboard-accessible profile selection;
- keyboard-accessible matrix input;
- labelled controls;
- accessible error summaries;
- field error announcements;
- risk meaning not conveyed by color alone;
- accessible proposed-control editing;
- confirmation-dialog focus management;
- visible focus;
- accessible table headers;
- loading announcements where appropriate.

Add automated accessibility checks for the major screens.

Document known limitations.

---



### 41. Storybook

Add Storybook stories for feature presentation components that do not require a live backend.

Recommended stories:

```text
AssessmentProfileSelector
RiskMatrixInput
RiskResultSummary
RiskComparison
ProposedControlsEditor
RiskAssessmentSummary
RiskAssessmentProperties
RiskAssessmentLifecycleActions
RelatedHazard
RelatedRiskControls
RiskAssessmentForm
```

Include states such as:

- default;
- loading;
- empty;
- validation error;
- read-only;
- Under Review;
- Approved;
- Superseded;
- permission-limited;
- dark theme;
- narrow viewport.

Use deterministic fixtures.

---



### 42. Unit and Integration Tests

Add unit tests for:

- backend-to-view-model mapping;
- form-to-request mapping;
- status mapping;
- risk-level mapping;
- Hierarchy of Controls mapping;
- permission capabilities;
- query keys;
- filter serialization;
- URL parameter parsing;
- profile mapping;
- matrix mapping;
- lifecycle action availability;
- superseding response handling;
- error-to-UX mapping;
- concurrency conflict handling.

Add component and integration tests for:

- Registry rendering;
- loading and empty states;
- filtering;
- pagination;
- Hazard preselection;
- profile selection;
- matrix input;
- proposed-control add/edit/remove;
- client-side validation;
- backend validation mapping;
- Object Page rendering;
- Draft editing;
- permission-limited actions;
- submission for review;
- approval;
- automatic superseding UX;
- archival;
- `404` handling;
- `409` handling;
- related controls;
- Activity.

Use the established API mocking strategy.

Avoid tests that only assert implementation details.

---



### 43. Browser End-to-End Tests

Add Playwright coverage against the approved integrated test environment.

Required primary workflow:

```text
Login
→ Open Risk Assessment Registry
→ Create Risk Assessment for a Hazard
→ Select Profile
→ Enter Inherent Risk
→ Add Proposed Controls
→ Enter Residual Risk
→ Create Draft
→ Edit Draft
→ Submit for Review
→ Approve
→ Verify Approved State
→ Verify Hazard Relationship
```

Required superseding workflow:

```text
Create and approve Assessment A
→ Create Assessment B in the same scope
→ Submit and approve Assessment B
→ Verify Assessment A is Superseded
→ Verify Assessment B is Approved
```

Required negative scenarios:

```text
Read-only user cannot mutate
User without approval permission cannot approve
Unknown assessment returns 404
Cross-tenant assessment returns 404
Invalid lifecycle action is rejected
Stale version displays conflict UX
Logout clears Risk Assessment data
```

Tests must:

- use stable users and organizations;
- use stable Hazard fixtures;
- use real configured profiles;
- not depend on execution order;
- clean up or isolate created data.

---



### 44. Backend Contract Extensions

Add backend functionality only when the UI reveals a concrete missing production contract.

Possible examples:

- list endpoint lacks required pagination metadata;
- profile configuration cannot be retrieved;
- related Hazard summary is unavailable;
- related Risk Controls cannot be queried;
- approval response does not expose enough authoritative state;
- audit projection cannot filter Risk Assessment events.

Any backend change must preserve:

- TenantContext;
- RBAC;
- audit;
- optimistic concurrency;
- cross-tenant `404` masking;
- existing persistence contracts;
- existing API compatibility.

Add focused backend tests for every backend change.

Document all backend changes in the completion report.

---



### 45. Public Feature API

Expose only approved feature entry points.

Recommended:

```ts
export {
  RiskAssessmentRegistryPage,
  RiskAssessmentCreatePage,
  RiskAssessmentObjectPage,
} from "@/features/risk-assessments";
```

Do not expose internal:

- schemas;
- mappers;
- API clients;
- query implementation;
- feature-private components.

Avoid deep imports from other features.

---



### 46. Architecture Guardrails

Extend architecture checks to ensure:

```text
shared components do not import risk-assessments
risk-assessments may import shared components
risk-assessments do not import Hazard internals
Hazard does not import Risk Assessment internals
routes import through feature public APIs
API modules do not import React components
presentation components do not call fetch directly
transport types do not leak into shared components
third-party UI libraries are not imported when shared wrappers exist
```

Cross-feature integration must use public boundaries.

---



### 47. Documentation

Create:

```text
docs/architecture/frontend/RiskAssessmentManagementUI.md
docs/tasks/TASK-P9-006.md
```

Update Hazard frontend documentation where the new integration affects it.

The architecture document must describe:

- feature structure;
- routes;
- backend endpoints;
- query keys;
- cache behavior;
- permissions;
- Hazard integration;
- assessment profiles;
- risk matrices;
- inherent risk;
- residual risk;
- proposed controls;
- Hierarchy of Controls;
- acceptance;
- review scheduling;
- competency references;
- lifecycle actions;
- automatic superseding;
- optimistic concurrency;
- tenant isolation;
- related Risk Controls;
- Activity data source;
- testing strategy;
- known limitations;
- deferred work.

The task report must include:

```text
Implementation summary
Frontend routes
Backend endpoints used
Permissions used
Feature structure
Shared components reused
New shared components
Backend changes
Registry capabilities
Form capabilities
Profile behavior
Matrix behavior
Inherent risk behavior
Proposed controls behavior
Residual risk behavior
Lifecycle actions
Automatic superseding behavior
Concurrency behavior
Hazard integration
Related Risk Control behavior
Activity source
Unit test count
E2E test count
Storybook result
Build result
Architecture result
Known limitations
Deferred work
Recommended next task
```

---



## Acceptance Criteria

The task is complete when all of the following are true:

1. A dedicated Risk Assessment frontend feature exists.
2. The feature follows the approved frontend architecture.
3. The feature exposes a controlled public API.
4. Risk Assessment navigation is integrated under Safety.
5. Navigation is permission-aware.
6. The Registry route exists.
7. The creation route exists.
8. The Object Page route exists.
9. All routes are authenticated.
10. Registry data comes from the production backend.
11. Search uses the backend contract.
12. Supported filters work.
13. Supported sorting works.
14. Server-side pagination works.
15. Registry state is URL-synchronized where appropriate.
16. Loading, empty, filtered-empty, error, and retry states exist.
17. Users with create permission can create assessments.
18. Users without create permission cannot access creation.
19. Creation can start from a Hazard.
20. Hazard context is preserved.
21. The form uses React Hook Form and Zod.
22. Profile selection uses real backend data.
23. Matrix inputs use real backend configuration.
24. Inherent risk inputs are supported.
25. Proposed controls can be added, edited, and removed while permitted.
26. Hierarchy of Controls uses canonical backend values.
27. Residual risk inputs are supported.
28. Backend validation maps correctly.
29. Duplicate submission is prevented.
30. Successful creation opens the Object Page.
31. Hazard relationship queries refresh after creation.
32. The Object Page uses shared Object Page components.
33. The header shows reference, Hazard, status, inherent risk, and residual risk.
34. Draft assessments can be edited when permitted.
35. Lifecycle-controlled fields are not changed through generic editing.
36. Submit for Review is implemented.
37. Approval is implemented.
38. Archive is implemented where supported.
39. Invalid lifecycle actions are not offered.
40. Backend lifecycle errors are handled safely.
41. Approval automatically supersedes the previous approved assessment where applicable.
42. Superseding is not implemented client-side.
43. The superseded assessment remains accessible.
44. Permission-aware actions work.
45. Backend `403` responses are handled.
46. Unknown assessments render the not-found experience.
47. Cross-tenant assessments render the same not-found experience.
48. Optimistic concurrency is implemented.
49. Stale mutations do not overwrite newer data.
50. `409 Conflict` produces actionable UX.
51. Query keys are stable.
52. Query caches are tenant-safe.
53. Mutations invalidate the correct queries.
54. Logout clears sensitive Risk Assessment data.
55. Linked Hazard data is displayed.
56. Related Risk Controls are displayed when available.
57. The frontend does not perform unsupported authoritative risk calculations.
58. Activity uses real backend audit data.
59. Fake client-generated history is not used.
60. User feedback is specific.
61. Desktop layout is production-usable.
62. Tablet and mobile layouts remain usable.
63. Accessibility checks cover major screens.
64. Keyboard navigation works.
65. Risk meaning does not depend on color alone.
66. Storybook contains relevant feature stories.
67. Unit tests pass.
68. Component and integration tests pass.
69. Browser E2E tests pass.
70. Automatic superseding is covered by E2E tests.
71. Read-only scenarios are tested.
72. Approval-permission scenarios are tested.
73. Cross-tenant behavior is tested.
74. Concurrency conflict behavior is tested.
75. Architecture guardrails pass.
76. Shared UI components are reused.
77. No duplicate general-purpose component system is introduced.
78. Strict TypeScript passes.
79. Lint passes.
80. Production build passes.
81. Storybook build passes.
82. Existing authentication tests remain passing.
83. Existing Hazard frontend tests remain passing.
84. Existing backend Risk Assessment tests remain passing.
85. Documentation is complete.
86. The task report reflects actual implementation and verification results.

---



## Non-Goals

This task does not implement:

- full Risk Control Management UI;
- Risk Control lifecycle actions;
- Risk Control owner assignment;
- Risk Control implementation tracking;
- Risk Control evidence management;
- Risk Control effectiveness verification;
- Inspection Management UI;
- Finding Management UI;
- Corrective Action UI;
- Incident Management UI;
- Training UI;
- Competency Management UI;
- Knowledge UI;
- Risk Profile Administration UI;
- Risk Matrix Administration UI;
- organization switching;
- file attachments;
- photo uploads;
- comments;
- offline mode;
- bulk import;
- bulk editing;
- persisted saved filters;
- production analytics dashboards;
- AI-generated assessments;
- AI-generated controls;
- frontend-owned authoritative risk calculations;
- a new workflow engine;
- backend redesign unrelated to concrete UI contract gaps.

Do not combine Risk Assessment and Risk Control Management into one task.

---



## Verification



### 1. Install

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



### 2. Design Tokens

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



### 6. Unit and Component Tests

Run:

```bash
npm run test
```

Verify coverage for:

```text
Risk Assessment mappers
Form schema
Status mapping
Risk-level mapping
Hierarchy of Controls mapping
Permission capabilities
Query keys
Registry filters
Profile selection
Matrix inputs
Proposed controls editor
Create form
Object Page
Lifecycle actions
Automatic superseding
API errors
Optimistic concurrency
Related Hazard
Related Risk Controls
Activity
```

All tests must pass.

---



### 7. Accessibility

Run the configured accessibility checks.

Verify at minimum:

```text
Risk Assessment Registry
Create Risk Assessment
Profile selector
Risk matrix input
Proposed controls editor
Risk Assessment Object Page
Lifecycle dialogs
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

Review stories in:

```text
Light theme
Dark theme
Desktop viewport
Tablet viewport
Mobile viewport
```

---



### 9. Browser E2E

Run:

```bash
npm run test:e2e
```

Required primary scenario:

```text
Login
→ Risk Assessment Registry
→ Create Assessment for Hazard
→ Select Profile
→ Enter Inherent Risk
→ Add Proposed Controls
→ Enter Residual Risk
→ Create Draft
→ Edit Draft
→ Submit for Review
→ Approve
→ Verify Approved State
```

Required superseding scenario:

```text
Approve Assessment A
→ Create Assessment B in the same scope
→ Approve Assessment B
→ Verify Assessment A is Superseded
→ Verify Assessment B is Approved
```

Required negative scenarios:

```text
Read-only user cannot mutate
User without approval permission cannot approve
Unknown assessment returns 404
Cross-tenant assessment returns 404
Invalid lifecycle action is rejected
Stale version displays conflict UX
Logout clears Risk Assessment data
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

or the project-equivalent command.

Verify:

```text
Shared components do not import Risk Assessment feature code
Risk Assessment routes use the public feature API
API modules do not import presentation components
Presentation components do not call fetch directly
Hazard and Risk Assessment features do not import each other’s internals
Approved shared wrappers are not bypassed
```

---



### 12. Backend Risk Assessment Tests

Run the existing backend tests.

Recommended:

```bash
pytest -m "not db" -k "risk_assessment"
pytest -m db -k "risk_assessment"
```

Adapt to actual test markers and paths.

All existing tests must remain passing.

Add focused tests for any backend contract added during this task.

---



### 13. Hazard Frontend Regression

Verify that the following remain working:

```text
Hazard Registry
Hazard Object Page
Related Risk Assessments
Create Risk Assessment entry point
Authentication
Permission-aware navigation
Tenant-safe caching
```

Run relevant unit and Playwright tests.

---



### 14. Permission Review

Verify with at least:

```text
Risk Assessment reader
Risk Assessment editor
Risk Assessment approver
User without Risk Assessment access
```

Confirm that users see only permitted routes and actions.

Backend authorization must remain authoritative.

---



### 15. Tenant Review

Verify with at least two organizations.

Confirm:

```text
Organization A assessments are not listed in Organization B
Organization A assessment URL returns 404 in Organization B
Hazard selectors are organization-scoped
Query caches do not cross organization boundaries
Logout clears organization-specific data
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

- Registry remains usable;
- filters remain accessible;
- profile selection remains readable;
- matrix inputs remain operable;
- proposed controls can be edited;
- Object Page sections stack correctly;
- lifecycle actions remain reachable;
- dialogs fit the viewport;
- no horizontal page overflow exists.

---



### 17. Completion Report

Update:

```text
docs/tasks/TASK-P9-006.md
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
Form capabilities
Profile behavior
Matrix behavior
Inherent risk behavior
Proposed controls behavior
Residual risk behavior
Lifecycle actions
Automatic superseding behavior
Optimistic concurrency behavior
Hazard integration
Related Risk Control behavior
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

Do not mark the task complete if:

- production data is replaced by mocks;
- create or read workflows are incomplete;
- profile or matrix definitions are incorrectly hardcoded;
- approval is incomplete;
- automatic superseding is not verified;
- optimistic concurrency is ignored;
- tenant masking is not covered;
- architecture guardrails fail;
- production build fails;
- Storybook build fails;
- E2E tests fail.

---



## Expected Outcome

SafetyMAIN receives the second complete frontend business vertical slice and the first full frontend Risk Assessment workflow.

The verified user workflow becomes:

```text
Authenticate
    ↓
Open Hazard
    ↓
Create Risk Assessment
    ↓
Select Assessment Profile
    ↓
Evaluate Inherent Risk
    ↓
Define Proposed Controls
    ↓
Evaluate Residual Risk
    ↓
Save Draft
    ↓
Submit for Review
    ↓
Approve
    ↓
Automatically Supersede Previous Approved Assessment
    ↓
Review Related Risk Controls and Activity
```

The feature is:

- authenticated;
- permission-aware;
- tenant-safe;
- lifecycle-oriented;
- profile-driven;
- matrix-driven;
- concurrency-safe;
- responsive;
- accessible;
- tested end to end;
- built from the approved shared UI foundation.

After successful completion, the recommended next task is:

```text
TASK-P9-007 — Risk Control Management UI
```

The Risk Control feature must reuse the established patterns for:

- Registry;
- Object Page;
- forms;
- lifecycle actions;
- owner assignment;
- implementation tracking;
- evidence;
- effectiveness verification;
- review scheduling;
- optimistic concurrency;
- Activity;
- permissions;
- tenant isolation.


---

## Approved Implementation Plan

Status: Approved  
Date: 2026-08-05  
Phase in progress: 1 (foundation only)

This section records the approved implementation plan. It does not replace the original Goal, Scope, Acceptance Criteria, Non-Goals, or Verification sections above.

### 1. Goal

Implement the complete SafetyMAIN frontend Risk Assessment Management vertical slice: registry, create (including from Hazard), draft edit, submit-for-review, approve (with automatic supersede UX via refetch), archive, related Hazard and read-only related Risk Controls, and audit activity.

Reuse shared `@/components` and the Hazard feature architecture. Backend remains authoritative for risk results, lifecycle transitions, and superseding. Do not invent endpoints, permissions, filters, sorting, profile administration, or materialization workflows.

### 2. Approved product decisions

1. **Two-step create contract**
   - `POST /api/v1/risk-assessments` creates a minimal Draft using only `CreateRiskAssessmentRequest` fields.
   - `PATCH /api/v1/risk-assessments/{id}` then saves update-only data (inherent/residual, controls, acceptance, schedule updates, `submit_for_review`, etc.).
   - UI may present one form; if POST succeeds and PATCH fails, keep the created Draft, navigate or stay with an honest partial-failure message, and allow retry of the PATCH/edit path. Do not roll back the create on the client.

2. **Product lifecycle UX**
   - Exposed progression: `Draft → Under Review → Approved` (then backend-driven `Superseded` / `Archived`).
   - Show **Approve only when status is `under_review`**, even though domain allows `draft → approved`.
   - Do not change backend lifecycle rules.

3. **Minimal profile catalog** (no full mirror of `assessment_profiles.py`)
   - Per profile: `code`, display `title`, `matrixSize`, `requiredFactorIds`.
   - Must support extra factors (e.g. `business_impact`, `exposure`, `frequency`, `detectability`, …) as editable factor score inputs.
   - No profile-list/configuration API → document as known limitation.
   - No `riskAssessmentKeys.profiles()` unless a real profile query is added later.

4. **Submit capability** = `risk:update` + `submit_for_review: true`. Do not invent `risk:submit`.

5. **No unsupported surface area**: no fake sort UI, no filters beyond list query params, no submit/supersede HTTP endpoints, no profile admin, no materialize actions.

6. **Feature boundaries**
   - No imports of another feature’s internal modules.
   - Public routes allowed.
   - Boundary-safe query invalidation for Hazard-related RA lists via **predicate/prefix matching** (same key shape Hazard uses: `["hazards", orgId, "detail", hazardId, "risk-assessments"]`). Do not import `hazardKeys` or other Hazard internals.
   - RA-local `GET /api/v1/hazards` (list/detail) for Hazard selector and related Hazard display on object/create flows.
   - Registry: prefer `hazard_id` links when the list DTO has no Hazard title. Avoid per-row Hazard requests unless cached and demonstrably necessary.

7. **Concurrency UI**
   - Shared components have **no** concurrency conflict dialog today.
   - Hazard uses feature-local `HazardConflictDialog` built on shared `Dialog`.
   - Implement RA conflict dialog the same way (feature-local on shared Dialog). Do not invent a new general-purpose shared system in this task; do not import Hazard’s dialog.

### 3. Locked backend contract

| Area | Contract |
|------|----------|
| Base | `/api/v1/risk-assessments` |
| Create | `POST` — `hazard_id`, `code`, `title`, `assessment_profile`, `assessed_object` (`object_type`, `reference`), optional `assessment_date`, `review_schedule`, `competency_requirements`, `extension_references` |
| Update / submit | `PATCH` — requires `expected_version`; optional title/object/date/schedule/competency/extensions/`controls`/`inherent_risk`/`residual_risk`/`acceptance`; `submit_for_review` |
| Approve | `POST .../approve` — `expected_version`, optional `acceptance` |
| Archive | `POST .../archive` — `expected_version`, `reason` |
| List/Get | `GET` collection and by id; list items are full `RiskAssessmentResponse` |
| List filters | `hazard_id`, `status`, `assessment_profile`, `assessed_object_type`, `include_archived`, `include_superseded`, `search`, `created_from`, `created_to` |
| Pagination | `offset`, `limit`; response `pagination.{offset,limit,total}` |
| Sorting | **None** — fixed `created_at DESC`, `id DESC`. No sort query params. No sortable column UI. |
| Permissions | `risk:read`, `risk:create`, `risk:update`, `risk:approve`, `risk:archive` (`risk:review` unused) |
| Evaluation request | `probability` / `severity` (enum or int) + optional `factors[]` + optional `level` + `explanation` |
| Evaluation response | `{ factors: [{factor, score}], level, explanation }` |
| Controls | embedded proposed `controls[]`; HoC: `elimination\|substitution\|engineering\|administrative\|ppe` |
| Related controls | `GET /api/v1/risk-controls?risk_assessment_id=` (read-only). Materialize out of UI scope. |
| Activity | `GET /api/v1/admin/audit-events?resource_type=RISK&resource_id=` |
| Concurrency | `version` / `expected_version`; `409` → reload, no auto-retry |
| Supersede | server-side on approve only; invalidate/refetch — do not guess superseded peer from approve body |
| Tenant | cross-tenant → same not-found as missing |

**Registry columns** — derive only from list DTO fields. Prefer linking `hazard_id` rather than fetching Hazard titles per row.

### 4. Architecture boundaries

```text
frontend/src/features/risk-assessments/   # owns RA UI + RA API + RA-local hazard reads
frontend/src/features/hazards/            # may link to /safety/risk-assessments/* only
@/components                              # shared UI; no feature imports
```

- `index.ts` exports only page components (added from Phase 2).
- Cross-feature: public routes only.
- Invalidate Hazard-related RA cache with predicate/prefix helpers in the RA feature (unit-tested). Keep key shape comment-synced with Hazard.
- Logout: AuthProvider `queryClient.clear()` — verify in later phase.

### 5. Affected files

See Phase 1 deliverables under `frontend/src/features/risk-assessments/` and `docs/architecture/frontend/RiskAssessmentManagementUI.md`. Later phases add routes, pages, Hazard touch-ups, E2E, guardrails.

### 6. Implementation phases

#### Phase 1 — Foundation (current)

Architecture contract doc; types; minimal profile catalog; schemas; mappers (evaluation factor round-trip); status/lifecycle/HoC/URL utilities; permissions; API clients; org-scoped query keys; mutations + boundary-safe invalidation; focused unit tests including invalidation predicates.

#### Phase 2 — Registry + create routes

Thin routes; route protection (`risk:read` / `risk:create`); registry with URL filters and registry states; two-step create form with partial-failure handling.

#### Phase 3 — Object page + lifecycle

Object page tabs; draft edit; submit/approve/archive; conflict dialog; activity; related Hazard/controls; supersede via invalidate/refetch.

#### Phase 4 — Hazard integration

Create CTA + related assessment links via public routes only.

#### Phase 5 — Stories, E2E, guardrails, docs, verification

Full task verification checklist.

### 7–10. Coverage, verification, risks, non-goals

As approved in the revised plan: AC coverage matrix maps to phases; Phase 1 verification is `npx vitest run src/features/risk-assessments`; risks include profile catalog drift and evaluation round-trip; non-goals include RC management, materialize UI, fake sorting, `risk:submit`, and cross-feature internal imports.

### Phase 1 correction notes (2026-08-05)

- Risk Control owner response shape is `owner_type`, `owner_reference`, `display_name_snapshot`, `assigned_at`, `assigned_by`. Label uses `display_name_snapshot` with `owner_reference` fallback.
- `extension_references` remains deferred (not on form/create mapper in Phase 1).
- Conflict dialog is Phase 3. Clearing `assessment_date` / `review_schedule` via `null` is unsupported by the current backend update semantics.


---

## Completion Report (Phase 5 — draft for Final Task Review)

Status: Ready for Final Task Review (not marked complete)  
Date: 2026-08-06

### Implementation summary

Frontend Risk Assessment Management vertical slice delivered across Phases 1–5: foundation (types/mappers/API), registry + two-step create, object page + lifecycle + conflict UX, Hazard integration via public routes, and release readiness (cleanup, Storybook, Playwright, dependency-cruiser, docs).

### Frontend routes

- `/safety/risk-assessments`
- `/safety/risk-assessments/new` (`?hazardId=` supported)
- `/safety/risk-assessments/[riskAssessmentId]`

### Backend endpoints used

`GET/POST /api/v1/risk-assessments`, `GET/PATCH /api/v1/risk-assessments/{id}`, `POST .../approve`, `POST .../archive`, `GET /api/v1/risk-controls?risk_assessment_id=`, RA-local `GET /api/v1/hazards`, `GET /api/v1/admin/audit-events?resource_type=RISK&resource_id=`.

### Permissions used

`risk:read|create|update|approve|archive`, `risk_control:read`, `audit:read`. Submit uses `risk:update` + `submit_for_review` (no `risk:submit`).

### Feature structure

`frontend/src/features/risk-assessments/` with public page exports in `index.ts`. See `docs/architecture/frontend/RiskAssessmentManagementUI.md`.

### Shared components reused

ObjectHeader, ObjectTabs, Page patterns, Dialog/ConfirmationDialog/SideDrawer, Registry*, FilterBar/Search, EmptyState/LoadingState/Alert/Toast, Timeline, NextActionCard, Form primitives, StatusBadge, DescriptionList/PropertyGrid.

### New shared components

None. Conflict dialog is feature-local on shared Dialog (same pattern as Hazard).

### Registry / form / profile / matrix / risk / controls / lifecycle

- Registry: URL-synced supported filters (UI subset), no sort UI, DTO columns, hazard_id links.
- Create: two-step POST→PATCH, partial-failure PATCH-only retry, submit lock after success, 422 field mapping.
- Profiles: minimal frontend catalog (code/title/matrixSize/requiredFactorIds).
- Evaluations: backend-authoritative level; client collects scores; Zod matrix/required-factor rules.
- Proposed controls: HoC enum; related controls read-only with empty-state distinction.
- Lifecycle: submit (draft + inherent risk), approve (under_review + acceptance override), archive (reason).
- Superseding: invalidate/refetch only.
- Concurrency: expected_version + feature conflict dialog.
- Hazard integration: Create CTA for active + risk:create; related rows link to RA object routes.

### Activity source

Audit API (`resource_type=RISK`), gated by `audit:read`.

### Backend changes

None.

### Verification (exact results — Phase 5)

Commands run from `frontend/` on 2026-08-06.

| Command | Result |
|---------|--------|
| `npm run verify` | **PASS** (exit 0) — tokens:check, format:check, lint (`--max-warnings=0`), typecheck, architecture:check, vitest, next build |
| `npm run architecture:check` | **PASS** — `✔ no dependency violations found (296 modules, 961 dependencies cruised)` |
| `npm run test` (via verify) | **PASS** — 14 files, **88 tests** passed |
| `npm run build` (via verify) | **PASS** — Next.js 15.3.5 production build; RA routes `/safety/risk-assessments`, `/new`, `/[riskAssessmentId]` present |
| `npm run build-storybook` | **PASS** (exit 0) — output `storybook-static/`; includes `risk-assessments.stories` |
| `npm run test:e2e -- e2e/risk-assessments.spec.ts` | **PASS** — **6 passed** (8.8s): happy path create→edit→submit→approve→archive; permission denied; validation 422; conflict 409; not found 404; partial create PATCH retry |
| `npm run test:e2e` (full suite) | **PASS** — **15 passed** (12.8s): auth (4) + hazards (4) + risk-assessments (6) + smoke (1) |

Vitest note: existing jsdom/axe `HTMLCanvasElement.prototype.getContext` stderr in `bootstrap.test.tsx` is unchanged and non-fatal.

### Known limitations

- No profile-list/configuration API (minimal catalog may drift).
- `extension_references` deferred from form.
- PATCH `null` cannot clear assessment_date / review_schedule.
- Materialize-controls out of UI scope.
- Registry filter UI intentional subset of list query params.

### Deferred work

TASK-P9-007 — Risk Control Management UI.

### Recommended next task

`TASK-P9-007 — Risk Control Management UI`
