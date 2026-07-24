# Layout System

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Navigation.md](Navigation.md) · [PageTemplates.md](PageTemplates.md) · [Responsive.md](Responsive.md)

---

## 1. Application shell

```text
┌──────────────────────────────────────────────────────────┐
│ Top navigation (org, search, alerts, user)               │
├──────────────┬───────────────────────────────────────────┤
│ Left nav     │ Content area                              │
│ (primary +   │  ┌─────────────────────────────────────┐  │
│  nested)     │  │ Page header / breadcrumbs / actions │  │
│              │  ├─────────────────────────────────────┤  │
│              │  │ Main content                        │  │
│              │  │                                     │  │
│              │  └─────────────────────────────────────┘  │
└──────────────┴───────────────────────────────────────────┘
```

| Region | Behavior |
|--------|----------|
| Top nav | Sticky; height 56px; org switcher, global search, notifications, help, user menu |
| Left nav | Sticky; expandable / collapsible; nested sections |
| Content | Scrolls independently; respects `layout.content.max` / `layout.object.max` |

## 2. Page width

| Template | Max width | Alignment |
|----------|-----------|-----------|
| Dashboard | 1440px | Centered in content pane |
| Registry | Fluid to content pane (min padding) | Full usable width |
| Object Page | 1120px (+ optional 360px related rail) | Content + side panel |
| Settings / Admin | 960–1120px | Centered |
| Wizard / Workflow | 720–880px | Centered focus |

## 3. Split layouts

| Pattern | Use |
|---------|-----|
| **Master–detail** | Registry list (40%) + detail preview (60%) on `lg+`; stack on smaller |
| **Object + related rail** | Main object (flex) + Related / Activity (360px) |
| **Split compare** | Rare — assessment versions side-by-side |

## 4. Panels

- `Panel`: bordered surface, `radius.lg`, optional header/actions.
- Nested panels avoid double borders; use subtle bg instead.
- Collapse panels on tablet when competing with primary task.

## 5. Drawers

| Property | Rule |
|----------|------|
| Width | 400px default; 560px for forms |
| Anchor | Right for detail / edit; left reserved for nav |
| Overlay | Dim canvas (`bg` at 40% opacity) |
| Focus | Trap focus; Esc closes; return focus to invoker |
| Stacking | Prefer replace over nested drawers |

Use drawers for secondary create/edit and quick views — not for primary Object Pages.

## 6. Modals (dialogs)

| Type | Use |
|------|-----|
| Confirm | Destructive or irreversible actions |
| Form (small) | ≤ 5 fields; else prefer drawer / page |
| Blocking | Rare — session expiry, fatal errors |

Max width: 480px (confirm), 640px (form). Always explicit primary + secondary actions.

## 7. Sticky regions

| Region | When |
|--------|------|
| Page header | Object Pages with long tabs |
| Command / action bar | Forms, wizards, registries with bulk actions |
| Table header | Registries with vertical scroll |
| Wizard stepper | Sticky top of workflow content |

Sticky bars use `color.bg.surface` + bottom border; `z.sticky`.

## 8. Fullscreen workflows

Wizards and multi-step assessments may enter **focused mode**:

- Hide left nav (or collapse to icon rail)
- Keep top nav minimal (exit, save draft, help)
- Centered workflow column

Exit must confirm if dirty.

## 9. Empty / loading chrome

Shell always renders; content region shows EmptyState / Skeleton / Error templates (see [PageTemplates.md](PageTemplates.md)).
