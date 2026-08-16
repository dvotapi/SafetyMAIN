# TASK-P9-007c — Risk Control Management UI: Materialization, Guardrails, E2E, Documentation

---

> **Part 3 of 3.** Depends on `TASK-P9-007a` and `TASK-P9-007b` (full
> Risk Control feature must exist first). Implements the umbrella
> specification's §9–§10, §46, §49–§50, §52: Risk Assessment
> materialization integration, extended architecture guardrails,
> Playwright end-to-end coverage, final documentation, and the
> consolidated completion report for the whole TASK-P9-007 umbrella.

## Context

This sub-task closes out TASK-P9-007. `TASK-P9-007a` delivered the
read-only Risk Control slice; `TASK-P9-007b` delivered every lifecycle
command. This sub-task connects the Risk Control feature back into the
Risk Assessment Object Page (materialization), locks the feature boundary
with dependency-cruiser rules, proves the full workflow end-to-end with
Playwright, and writes the final documentation, including the umbrella
completion report in `docs/tasks/TASK-P9-007.md`.

## Scope

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

## Acceptance Criteria (subset of TASK-P9-007)

The task is complete when all of the following are true:

16. Risk Assessment materialization uses the production endpoint.
17. Materialization is permission-aware.
18. Duplicate materialization handles `409`.
19. Materialization does not mutate Risk Assessment state client-side.
20. Created Risk Controls appear in related views.
71. Browser E2E tests pass.
72. Materialization is covered by E2E.
73. Owner assignment is covered by E2E.
74. Implementation flow is covered by E2E.
75. Evidence addition is covered by E2E.
76. Effectiveness verification is covered by E2E.
77. Review scheduling is covered by E2E.
79. Cross-tenant behavior is tested.
81. Duplicate materialization is tested.
82. Architecture guardrails pass.
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

Run:

```bash
cd frontend && npm run verify && npm run architecture:check && npm run build-storybook && npm run test:e2e
```

Required E2E scenarios: the full materialize → assign owner → plan →
start → progress → evidence → complete → verify → schedule review flow;
all three effectiveness outcomes as distinct states; every negative
scenario from the umbrella spec §46 (read-only user, no-verify-permission
user, unknown control 404, cross-tenant control 404, stale version
conflict, duplicate materialization conflict, invalid lifecycle action,
logout clears data).

Backend regression:

```bash
python -m pytest && python -m ruff check .
```

Do not mark this sub-task — or the umbrella TASK-P9-007 — complete if
materialization is incomplete, architecture guardrails fail, or any E2E
test fails.

---

## Completion Report

Status: **Complete.** Delivered per the acceptance criteria and
Verification section above (materialization workflow, deferred-work and
documentation cleanup, Playwright E2E coverage). This sub-task's work is
folded into the umbrella completion report — see `TASK-P9-007.md`
§ Completion Report for the consolidated implementation summary,
verification results, and commit range covering `TASK-P9-007a`,
`TASK-P9-007b`, and `TASK-P9-007c` together.
