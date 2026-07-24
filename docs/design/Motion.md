# Motion

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Accessibility.md](Accessibility.md) · [Principles.md](Principles.md)

---

## 1. Principle

Motion improves orientation and feedback. It must not decorate.

## 2. Allowed uses

| Use | Guidance |
|-----|----------|
| Page / route enter | Subtle fade or short slide ≤ 150–200ms |
| Dialog / drawer | Enter/exit 150–250ms; opacity + translate |
| Loading | Skeleton pulse low-contrast; indeterminate progress |
| Expansion | Accordion height animation ≤ 200ms |
| Toasts | Slide/fade; auto-dismiss with pause on hover/focus |

## 3. Disallowed

- Looping ornamental animations
- Parallax, bounce, and elastic overshoot in enterprise chrome
- Delaying primary content visibility for flourish

## 4. Timing tokens (planned)

| Token | ms |
|-------|----|
| `motion.fast` | 120 |
| `motion.normal` | 180 |
| `motion.slow` | 250 |

Easing: standard ease-out for entrances; ease-in for exits.

## 5. Reduced motion

When `prefers-reduced-motion: reduce`:

- Replace transitions with instant state changes or opacity-only ≤ 100ms
- Disable skeleton pulse; use static skeleton
