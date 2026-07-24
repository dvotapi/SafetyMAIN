# Status Language

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [LifecycleRules.md](../domain/LifecycleRules.md) · [Tokens.md](Tokens.md) · [ComponentCatalog.md](ComponentCatalog.md)

---

## 1. Purpose

A single visual grammar for lifecycle and operational states across Hazard, Risk Assessment, Risk Control, and future domains (Inspection, Incident, Training…).

**Domain transitions remain authoritative** in LifecycleRules. This document only maps those states to UI.

## 2. Badge anatomy

```text
┌────────────────────────────┐
│ [icon]  Label text         │
└────────────────────────────┘
```

| Property | Rule |
|----------|------|
| Component | `StatusBadge` |
| Shape | `radius.sm`, pill **not** required; prefer soft rectangle |
| Height | 22–24px compact; 28px comfortable |
| Label | Always visible; never color-only |
| Icon | Optional but recommended for critical / terminal / overdue |
| Contrast | Text/icon vs badge background ≥ 4.5:1 |

## 3. Semantic status tokens

| Token | FG | BG | Border |
|-------|----|----|--------|
| `color.status.draft` | slate.700 | slate.100 | slate.300 |
| `color.status.review` | blue.800 | blue.50 | blue.200 |
| `color.status.approved` | green.800 | green.50 | green.200 |
| `color.status.rejected` | red.800 | red.50 | red.200 |
| `color.status.planned` | teal.800 | teal.50 | teal.200 |
| `color.status.active` | teal.900 | teal.100 | teal.300 |
| `color.status.inProgress` | blue.800 | blue.50 | blue.200 |
| `color.status.implemented` | slate.800 | slate.100 | slate.300 |
| `color.status.effective` | green.900 | green.100 | green.300 |
| `color.status.partial` | amber.900 | amber.100 | amber.300 |
| `color.status.ineffective` | red.900 | red.100 | red.300 |
| `color.status.overdue` | amber.950 | amber.200 | amber.500 |
| `color.status.suspended` | amber.900 | amber.50 | amber.300 |
| `color.status.archived` | slate.600 | slate.100 | slate.300 |
| `color.status.cancelled` | slate.600 | slate.50 | slate.200 |
| `color.status.superseded` | slate.700 | slate.100 | slate.400 |

Do not reuse `effective` green for generic “success toasts” without also using success tokens; status greens are reserved for effectiveness / approval outcomes.

## 4. Canonical status catalog

| Status | Token | Icon key | Domains |
|--------|-------|----------|---------|
| Draft | `draft` | `file-pen` | Hazard, RA, Control, … |
| Under Review | `review` | `eye` | RA |
| Approved | `approved` | `badge-check` | RA |
| Rejected | `rejected` | `badge-x` | RA |
| Planned | `planned` | `calendar-clock` | Control, Inspection |
| Active | `active` | `circle-check` | Hazard |
| In Implementation | `inProgress` | `loader` | Control |
| Implemented | `implemented` | `package-check` | Control |
| Verified Effective | `effective` | `shield-check` | Control |
| Verified Partially Effective | `partial` | `shield-alert` | Control |
| Verified Ineffective | `ineffective` | `shield-x` | Control |
| Overdue | `overdue` | `clock-alert` | Control review, tasks |
| Suspended | `suspended` | `pause` | Control |
| Archived | `archived` | `archive` | All |
| Cancelled | `cancelled` | `ban` | Control, RA |
| Superseded | `superseded` | `replace` | Control, RA |

### Compound indicators

Overdue is an **operational overlay**, not always a lifecycle state. Show:

1. Lifecycle `StatusBadge`
2. Separate overdue chip / alert when `is_overdue` / review due

Never paint an entire Approved assessment as overdue-amber because a related control is overdue — overdue attaches to the overdue object.

## 5. Accessibility

- Include visible text; do not rely on hue.
- Provide `aria-label` when badge is the only status cue in a dense cell (e.g. `Status: Verified Ineffective`).
- Overdue must also appear in text filters / columns, not only color.
- High-contrast theme boosts borders; keep labels.

## 6. Consistency rules

1. One status string → one token → one badge style, globally.
2. New domain statuses must extend this table; do not invent local colors.
3. Terminal states (`Archived`, `Cancelled`, `Superseded`) use muted neutrals, not success green.
4. Destructive lifecycle actions use danger buttons; badges stay status-colored.
