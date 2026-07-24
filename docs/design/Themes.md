# Theme System

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Tokens.md](Tokens.md) · [StatusLanguage.md](StatusLanguage.md) · [Accessibility.md](Accessibility.md)

---

## 1. Themes

| Theme | Role |
|-------|------|
| **Light** | Default product theme |
| **Dark** | Supported alternate; same structure |
| **High contrast** | Readiness only in P9-001 — token hooks reserved |

All themes share one semantic token schema. Components never hardcode Light hex values.

## 2. Light (default)

Defined in [Tokens.md](Tokens.md) semantic table — canvas slate.50, surfaces white, primary teal.500.

## 3. Dark remapping (normative intent)

| Semantic | Dark direction |
|----------|----------------|
| `color.bg.canvas` | slate.900 / near `#0E1418` |
| `color.bg.surface` | slate.800 |
| `color.bg.subtle` | slate.700/800 mix |
| `color.border.default` | slate.600 |
| `color.text.primary` | slate.50 |
| `color.text.secondary` | slate.300 |
| `color.text.muted` | slate.400 |
| `color.interactive.default` | teal.300–400 (maintain contrast) |
| Status backgrounds | Darkened ramps; borders strengthen |
| Shadows | Prefer border elevation; reduce blur glow |

Exact hex pairs are finalized at token-codegen time; contrast must pass AA for text and badges.

## 4. High contrast readiness

Reserve:

- Stronger borders (`color.border.strong` forced)
- No reliance on low-opacity fills alone
- Focus ring thickness ≥ 3px

A full high-contrast theme pack is **Planned**, not shipped in P9-001.

## 5. User preference

- Default: Light
- Respect OS `prefers-color-scheme` when user selects System
- Persist explicit Light/Dark in user settings (implementation task)

## 6. Charts & media

Chart palettes must provide dark variants. Do not invert images of status badges — re-token them.
