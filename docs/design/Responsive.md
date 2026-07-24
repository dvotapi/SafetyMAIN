# Responsive Strategy

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Layout.md](Layout.md) · [Tokens.md](Tokens.md) · [Accessibility.md](Accessibility.md)

---

## 1. Priority

| Surface | Priority | Notes |
|---------|----------|-------|
| Desktop (`xl`+) | **Primary** | Full registries, admin, analytics |
| Laptop (`lg`) | Primary | Collapsible nav acceptable |
| Tablet (`md`) | **Inspections & review** | Master–detail, large touch targets |
| Mobile (`sm`) | **Field operations** | Queues, capture refs, approve lightweight actions |

Design desktop-first, then adapt. Do not ship mobile-only patterns that break registries.

## 2. Breakpoint behavior

| Area | `lg+` | `md` | `< md` |
|------|-------|------|--------|
| Left nav | Persistent | Drawer | Drawer / sheet |
| Registry | Full grid | Horizontal scroll OK | Card list fallback optional |
| Object Page | Main + rail | Stack rail below | Tabs only; rail as tab |
| Dialogs | Centered | Centered | Fullscreen sheet preferred |
| CommandBar | Inline | Inline wrap | Bottom sticky actions |

## 3. Touch

- Minimum target `44×44` px on tablet/mobile primary actions.
- Density “Comfortable” default on touch; Compact desktop-only.

## 4. Field operations (mobile)

Supported jobs:

- View assigned tasks / overdue controls
- Add evidence **reference**
- Complete simple checklist steps (future Inspection)

Not optimized initially:

- Heavy grid configuration
- Admin membership matrices
- Complex assessment editing

## 5. Testing

Verify critical templates at 375, 768, 1280, 1440 widths.
