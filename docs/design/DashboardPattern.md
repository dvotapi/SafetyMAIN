# Dashboard Pattern

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [PageTemplates.md](PageTemplates.md) · [StatusLanguage.md](StatusLanguage.md)

---

## 1. Primary question

> What requires attention right now?

Dashboards optimize for triage, not decoration.

## 2. Information order

1. **Alerts** — critical / overdue / failed verifications  
2. **My tasks / work queue** — assigned actions with due dates  
3. **KPI cards** — countable operational metrics  
4. **Upcoming work** — scheduled reviews, inspections  
5. **Charts / heatmaps** — trend context  
6. **Recent activity** — audit-flavored feed  

Do not lead with vanity charts above alerts.

## 3. Building blocks

| Block | Rules |
|-------|-------|
| KPI card | One metric, label, optional delta, link to filtered registry |
| Alert list | Severity icon + object link + age |
| Task queue | Object, action verb, due, status |
| Chart | Max one primary insight per chart; legend accessible |
| Heatmap | Risk / location intensity; tooltip with counts |
| Activity | Reuse ActivityFeed pattern |

## 4. Scope controls

- Personal vs organization toggle
- Time range (7 / 30 / 90 days) where meaningful
- Safety subdomain filters (Hazards, Controls…)

## 5. Density

Comfortable spacing (`layout.section.gap`). Avoid packing > 8 KPI cards above the fold.

## 6. Empty dashboard

If no alerts/tasks: calm EmptyState with guidance (“No overdue controls”) — not fake demo charts.
