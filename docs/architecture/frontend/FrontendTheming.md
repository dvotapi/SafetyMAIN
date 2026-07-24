# Frontend Theming

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-002

Related: [Design Tokens](../../design/Tokens.md) · [Themes](../../design/Themes.md)

## Canonical source

`frontend/src/theme/tokens/tokens.json`

## Generation

```bash
npm run tokens:build   # writes src/theme/generated/tokens.css + tokens.ts
npm run tokens:check   # fails if generated output is stale
```

Prefix: `--sm-*`.

## Modes

| Mode | Behavior |
|------|----------|
| `system` | Follows `prefers-color-scheme` |
| `light` | Forces light semantic map |
| `dark` | Forces dark semantic map |

Persisted in `localStorage` key `safetymain.theme-mode`.

Anti-flash: inline `themeInitScript` in root layout sets `data-theme` before paint.

## Consumption rules

Components use semantic CSS variables (`var(--sm-color-text-primary)`), not raw palette hex.

Raw palette values exist only in token source / generated `:root` palette vars for theme authoring.
