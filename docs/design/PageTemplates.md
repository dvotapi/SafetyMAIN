# Page Templates

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Layout.md](Layout.md) · [DashboardPattern.md](DashboardPattern.md) · [RegistryPattern.md](RegistryPattern.md) · [WorkflowPattern.md](WorkflowPattern.md)

---

## 1. Template inventory

| Template | Primary use |
|----------|-------------|
| Dashboard | Attention, KPIs, queues |
| Registry | Large searchable collections |
| Object Page | Single business object |
| Wizard | Multi-step create / guided flows |
| Workflow | Lifecycle stage visualization + actions |
| Analytics | Charts, heatmaps, saved reports |
| Settings | User / module preferences |
| Administration | Tenant admin registries + forms |
| Empty State | No data / no access / first run |
| Not Found | Unknown route or masked 404 |
| Error | Recoverable / fatal page errors |
| Loading | Skeletons while fetching |

Every template defines: **header, actions, breadcrumbs, filters (if any), content, secondary panels, activity (if any), footer/meta**.

---

## 2. Universal Object Page

Standard layout for Hazard, Risk Assessment, Risk Control, and future objects.

```text
┌ Breadcrumb ─────────────────────────────────────────────┐
├ Header: title · code · StatusBadge · CommandBar ────────┤
├ Summary strip (key properties + risk/severity cues) ───┤
├ Tabs: Summary | …domain tabs… | Timeline | Related | Activity ┤
├──────────────────────────────────────┬──────────────────┤
│ Tab content                          │ Related / Meta   │
│                                      │ (optional rail)  │
└──────────────────────────────────────┴──────────────────┘
```

### Regions

| Region | Content |
|--------|---------|
| **Header** | Title, business code, status, primary lifecycle actions |
| **Summary** | 4–8 key fields (owner, dates, severity, scope) |
| **Status** | `StatusBadge` + overdue overlay if applicable |
| **Actions** | CommandBar: next lifecycle CTA + overflow (suspend, archive…) |
| **Tabs** | Domain-specific + Timeline + Related + Activity |
| **Timeline** | Status changes, audit, comments (see Timeline) |
| **Related Objects** | Typed links (Assessment → Controls → Inspections) |
| **Activity** | Filtered stream; may merge with Timeline tab |

### Rules

1. All business objects reuse this skeleton.
2. Domain tabs vary; chrome does not.
3. Primary CTA = next valid transition from domain rules.
4. No DELETE affordance when API has no DELETE (e.g. Risk Control).
5. Optimistic concurrency: include `version` in mutations; map 409 to conflict dialog.

### Examples

Hazard · Risk Assessment · Risk Control · Inspection · Incident · Training · Instruction · Employee

---

## 3. Dashboard template

See [DashboardPattern.md](DashboardPattern.md).

Header: greeting / org context · date range · personal scope toggle.  
Content: alerts → my tasks → KPIs → charts → recent activity.

---

## 4. Registry template

See [RegistryPattern.md](RegistryPattern.md).

Header + FilterBar + DataGrid + pagination + bulk CommandBar.

---

## 5. Wizard template

Centered column, sticky stepper, Back / Continue / Save draft.  
Used for create flows that exceed one screen (e.g. initial Risk Assessment).

---

## 6. Workflow template

See [WorkflowPattern.md](WorkflowPattern.md).  
May embed inside Object Page (Summary tab) or fullscreen focused mode.

---

## 7. Analytics template

FilterBar + chart canvas + optional data table. Chart library choice is implementation-time; layout density matches Dashboard.

---

## 8. Settings / Administration

Settings: grouped forms, autosave optional.  
Administration: Registry + Object Page for users, memberships, audit log viewers.

---

## 9. Empty / Not Found / Error / Loading

| Template | Guidance |
|----------|----------|
| Empty State | Icon, title, one sentence, one CTA (Create / Clear filters) |
| Not Found | Neutral copy; no existence leak across tenants (align with API 404 masking) |
| Error | What failed, correlation id if any, Retry / Go back |
| Loading | Skeleton matching final layout — not a centered spinner alone for pages |

---

## 10. Footer / meta

Object Pages show created/updated metadata in Summary or a Meta disclosure — not a site-wide marketing footer.
