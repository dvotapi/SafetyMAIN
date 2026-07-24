# Accessibility

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Principles.md](Principles.md) · [StatusLanguage.md](StatusLanguage.md) · [Forms.md](Forms.md)

---

## 1. Target

Meet **WCAG 2.2 Level AA** where practical for product chrome, registries, and Object Pages.

## 2. Keyboard

- All actions reachable via keyboard.
- Logical tab order; no keyboard traps except modals/drawers (with Esc).
- Registries: arrow-key navigation planned for DataGrid; minimum Tab to row actions.
- Skip link to main content required in shell.

## 3. Focus

- Visible focus ring using `color.focus.ring` (never `outline: none` without replacement).
- Focus restored to invoker when overlays close.
- Route changes move focus to page `h1` or main.

## 4. Contrast

- Text vs background ≥ 4.5:1 (3:1 for large text).
- Status badges meet contrast on their token pairs.
- Charts require non-color cues (patterns/labels).

## 5. Screen readers

- Landmarks: `banner`, `navigation`, `main`, `complementary`.
- Status badges expose textual status.
- Icon-only controls have names.
- Live regions for toasts and autosave (“Saved”).
- Tables: proper headers; sort state announced.

## 6. Color independence

Severity and status always include text and/or icon — never hue alone.

## 7. Touch targets

≥ 44×44 px for primary mobile/tablet controls; desktop compact may use 28–36 height with adequate spacing.

## 8. Motion

Honor `prefers-reduced-motion` (see [Motion.md](Motion.md)).

## 9. Auth / tenant

Error copy must not leak cross-tenant resource existence (align with API 404 masking).
