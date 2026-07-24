# Registry Pattern

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [PageTemplates.md](PageTemplates.md) · [Forms.md](Forms.md) · [ComponentCatalog.md](ComponentCatalog.md)

---

## 1. Purpose

Operate over **thousands of records** with predictable performance and scannable density.

Used for: Hazards, Risk Assessments, Risk Controls, Inspections, Users, Audit events, etc.

## 2. Anatomy

```text
┌ Header (title, primary Create, view switcher) ──────────┐
├ FilterBar (search, facets, saved views) ────────────────┤
├ CommandBar (bulk actions when selection > 0) ───────────┤
├ DataGrid (sticky header, selectable rows) ──────────────┤
├ Pagination / result count ──────────────────────────────┘
```

## 3. Capabilities

| Capability | Requirement |
|------------|-------------|
| Sorting | Server-side for large sets; indicate active column |
| Filtering | Facets aligned with API filters; invalid values surfaced |
| Saved views | Named filter+column presets per user (planned persistence) |
| Column config | Show/hide/reorder; persist per view |
| Pagination | Page size 25/50/100; stable sort tie-breaker (id/code) |
| Bulk actions | Only when domain allows; confirm destructive |
| Search | Debounced; searches code + title by default |
| Selection | Checkbox column; select page vs select filtered (explicit) |
| Density | Comfortable / Compact modes |

## 4. Columns

Default columns prioritize: **code, title, status, owner, updated, overdue cue**.  
UUID columns hidden by default.

Status always via `StatusBadge`.

## 5. Performance UX

- Skeleton rows on first load
- Keep previous rows visible during refetch when possible
- Empty filter results ≠ error
- Cross-tenant: empty / 404 semantics — never leak existence

## 6. Master–detail (optional)

On wide screens, selecting a row may open a detail preview pane without leaving the registry. Full Object Page remains the system of record view.

## 7. Components

`FilterBar`, `DataGrid`, `CommandBar`, `Pagination`, `SavedViewSwitcher`, `EmptyState`.
