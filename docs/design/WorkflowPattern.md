# Workflow Pattern

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [PageTemplates.md](PageTemplates.md) · [StatusLanguage.md](StatusLanguage.md) · [LifecycleRules.md](../domain/LifecycleRules.md)

---

## 1. Intent

Visualize **lifecycle**, not form steps alone. Users should see where the object is, what comes next, and what blocks progress.

## 2. Safety value chain (reference)

```text
Identify → Assess → Control → Verify → Review
```

Maps conceptually to Hazard → Risk Assessment → Risk Control → Verification → Review schedule.

Object-specific steppers use that object’s lifecycle (e.g. Control: Draft → Planned → In Implementation → Implemented → Verified…).

## 3. WorkflowStepper

| Element | Behavior |
|---------|----------|
| Steps | Ordered stages; completed / current / upcoming / blocked |
| Current | Emphasized with `interactive` tokens |
| Completed | Check icon + muted success |
| Blocked | Warning icon + reason tooltip / helper |
| Next action | Explicit button beneath stepper (`Plan`, `Start implementation`…) |
| Progress | Optional thin progress for linear flows only |

Non-linear branches (e.g. Effective vs Ineffective) show alternate paths without fake linearization.

## 4. States

| UI state | Meaning |
|----------|---------|
| Current stage | Domain status of the aggregate |
| Next action | Highest-priority permitted transition for the actor |
| Blocked | Missing prerequisites (owner, evidence, approval) |
| Completed | Terminal success path for this chain |
| Cancelled / Superseded / Archived | Terminal exits — stepper collapses to status summary |

## 5. Placement

1. Object Page Summary — compact stepper.
2. Fullscreen Workflow template — large stepper + stage checklist.
3. Dashboard task cards — single next action, link to object.

## 6. Copy rules

- Verbs match domain commands (`Approve`, not `Submit for good`).
- Blocked reasons cite missing fields / permissions.
- Never invent transitions that LifecycleRules disallow.

## 7. Component

Catalog entry: `WorkflowStepper` (+ optional `WorkflowStagePanel` for checklist body).
