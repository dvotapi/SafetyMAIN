# TASK-P9-007b — Risk Control Management UI: Lifecycle & Workflow Commands

---

> **Part 2 of 3.** Depends on `TASK-P9-007a` (read-only slice, types,
> mappers, permissions, registry, Object Page shell must exist first).
> Implements the umbrella specification's §16–§27, §29–§36, §44–§45, §51:
> every Risk Control lifecycle command — owner assignment, implementation
> planning, start, progress, evidence, completion, effectiveness
> verification, review scheduling/completion, suspend/resume, supersede,
> cancel, archive — plus optimistic concurrency, Storybook coverage for
> the new components, and unit/component tests.
>
> Risk Assessment materialization, architecture guardrails, E2E tests, and
> final documentation are out of scope here — see `TASK-P9-007c`.

## Context

This sub-task builds directly on top of the feature scaffold, types,
mappers, query keys, and read-only Object Page delivered by
`TASK-P9-007a`. Read that task's completion report before starting.

The production Risk Control backend already supports every command listed
below (`TASK-P8-004`, `TASK-P8-004-H1`). No backend changes are expected
in this sub-task; if the frontend reveals a genuine missing contract,
follow the same Backend Contract Extensions constraints as the umbrella
task (§47) and get it reviewed before changing backend code.

## Scope

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

## Acceptance Criteria (subset of TASK-P9-007)

The task is complete when all of the following are true:

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
45. Review completion works where supported.
46. Suspend/Resume works where supported.
47. Supersede works where supported.
48. Cancel works where supported.
49. Archive works where supported.
50. No DELETE action exists.
51. Permission-aware actions work.
55. Optimistic concurrency is implemented.
56. Stale writes do not overwrite newer data.
57. `409 Conflict` provides actionable UX.
63. User feedback is specific.
68. Storybook contains relevant Risk Control stories.
69. Unit tests pass.
70. Integration/component tests pass.
78. Read-only permission scenarios are tested.
80. Concurrency conflict behavior is tested.
92. Existing backend Risk Control tests remain passing.
93. Correction-record behavior remains deferred.

---

## Non-Goals

In addition to the umbrella Non-Goals, this sub-task explicitly excludes:

- Risk Assessment materialization integration — `TASK-P9-007c`.
- Architecture guardrail changes — `TASK-P9-007c`.
- Playwright end-to-end coverage — `TASK-P9-007c`.
- Final consolidated documentation and completion report — `TASK-P9-007c`.

---

## Verification

Run:

```bash
cd frontend && npm run verify && npm run build-storybook
```

Coverage must include: owner request mapping, implementation request
mapping, evidence mapping, verification mapping, review mapping, conflict
handling, lifecycle action availability, optimistic concurrency.

Run the configured accessibility checks against: Object Page, owner form,
implementation form, evidence form, verification form, review schedule
form, every lifecycle confirmation dialog, and the conflict dialog. No
critical automated accessibility violations are allowed.

Do not mark this sub-task complete if any lifecycle command is missing,
partial effectiveness is collapsed into another state, optimistic
concurrency is ignored, verification history can be rewritten, or the
Storybook build fails.
