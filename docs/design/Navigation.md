# Navigation Architecture

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Layout.md](Layout.md) · [Iconography.md](Iconography.md) · [FrontendArchitecture.md](FrontendArchitecture.md)

---

## 1. Goals

- Scale across Safety, People, Knowledge, Analytics, and Administration without redesign.
- Mirror how work is organized, not how tables are named.
- Keep nested routes discoverable and deep-linkable.

## 2. Primary navigation

| Section | Purpose | Icon |
|---------|---------|------|
| **Overview** | Personal attention queue, KPIs, alerts | `layout-dashboard` |
| **Safety** | Hazard → Assessment → Control → Inspection → Incident | `shield-check` |
| **People** | Employees, competence, assignments | `users` |
| **Knowledge** | Knowledge objects, instructions, documents | `book-open` |
| **Analytics** | Reports, trends, heatmaps | `chart-column` |
| **Administration** | Users, org, membership, audit, settings | `settings` |

Order is fixed. New top-level sections require Design System review.

## 3. Nested navigation (Safety example)

```text
Safety
├── Hazards
├── Risk Assessments
├── Risk Controls
├── Inspections          (planned)
├── Findings             (planned)
└── Incidents            (planned)
```

Rules:

1. Nest by domain affinity, not by CRUD verb.
2. Badge counts on nav items are reserved for attention (overdue, assigned to me) — optional.
3. Items the user cannot access (RBAC) are hidden, not disabled with tease.

## 4. Secondary navigation

Inside Object Pages, use **Tabs** (Summary, Controls, Timeline, Related, Activity) — not a second left rail.

Settings / Administration may use vertical subnav within content.

## 5. Breadcrumbs

```text
Safety / Risk Controls / RC-1042 — Machine Guarding
```

- Always include section root.
- Last crumb is current page (not a link).
- Object codes preferred over bare UUIDs.

## 6. Org / tenant context

Top nav exposes current organization. Switching org:

- Clears object context
- Routes to Overview of the new org
- Never silently keeps previous org’s object URL active

## 7. Global search

Top-nav search queries across permitted object types; results grouped by type with status badges.

## 8. Scalability

Adding Inspection Management:

1. Add nested item under Safety.
2. Reuse Registry + Object Page templates.
3. No new primary section unless it spans multiple domains.

## 9. Responsive nav

| Breakpoint | Behavior |
|------------|----------|
| `lg+` | Persistent left nav |
| `md` | Collapsible drawer nav |
| `< md` | Bottom or hamburger + drawer; desktop patterns remain primary design target |
