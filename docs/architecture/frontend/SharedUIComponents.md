# Shared UI Component Library

Status: Active  
Date: 2026-07-25  
Task: [TASK-P9-003](../../tasks/TASK-P9-003.md)

Related: [Design System](../../design/README.md) · [FrontendArchitecture](FrontendArchitecture.md)

## Public import

```ts
import { Button, DataTable, ObjectHeader, Dialog } from "@/components";
```

Prefer the barrel over deep paths.

## Layers

| Folder | Responsibility |
|--------|----------------|
| `primitives/` | Buttons, inputs, selects, labels, status |
| `layouts/` | Container, Stack, Grid, SplitView, ResizablePanel |
| `navigation/` | Top/Side nav, Tabs, Breadcrumbs, CommandBar, menus |
| `dialogs/` | Dialog, confirmations, drawers, ModalStack |
| `feedback/` | Alert, Toast, Empty/Loading, Progress |
| `data-display/` | PropertyGrid, Avatar, Chip, **DataTable** |
| `filters/` | FilterBar, chips, date range, saved filters placeholder |
| `forms/` | Form sections, RHF adapters, validation summary |
| `workflow/` | Stepper, next action, blocking reason, review banner |
| `timeline/` | Grouped event timeline |
| `activity/` | Activity feed atoms |
| `object-page/` | ObjectHeader/Summary/Tabs/Relationships/… |
| `registry/` | Registry toolbar/table/pagination composition |
| `dashboard/` | KPI/Task/Alert cards + chart placeholders |

## Rules

1. Shared components never import `features/*`.
2. Consume semantic tokens (`--sm-*`) only.
3. Map backend enums in features — primitives stay domain-neutral (`VisualStatus`).
4. Icons only via `@/icons` wrapper (no direct Lucide in features).

## Accessibility

Keyboard focus, ARIA on interactive controls, status text not color-alone, `prefers-reduced-motion` honored in feedback/progress.

## Storybook

```bash
npm run storybook
npm run build-storybook
```

Stories cover key primitives, DataTable, Dialog, navigation, workflow, timeline, filters, object header. Theme addon switches light/dark.

## Deferred

Permission-aware nav, real charts, server-side table, i18n, business screens — later tasks.
