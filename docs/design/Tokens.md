# Design Tokens

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Themes.md](Themes.md) · [StatusLanguage.md](StatusLanguage.md) · [ComponentCatalog.md](ComponentCatalog.md)

---

## 1. Rules

1. **No hardcoded visual values in components.** Reference tokens only.
2. Semantic tokens (`color.text.primary`, `space.4`) wrap primitive scales.
3. Themes remap semantic tokens; components never branch on theme name for color.
4. Token names are stable API; raw palette values may change behind them.

Naming convention (implementation-ready):

```text
{category}.{role}.{variant?}
```

Examples: `color.bg.canvas`, `color.status.overdue`, `space.3`, `radius.md`, `shadow.sm`.

---

## 2. Typography

### Font family

| Token | Value | Usage |
|-------|-------|-------|
| `font.family.sans` | `"IBM Plex Sans", "Segoe UI", system-ui, sans-serif` | UI body, labels, navigation |
| `font.family.display` | `"IBM Plex Sans", …` | Page titles (same family, heavier weight) |
| `font.family.mono` | `"IBM Plex Mono", ui-monospace, monospace` | Codes, IDs, audit hashes, technical values |

Rationale: IBM Plex is enterprise-legible, distinct from default Inter/Roboto stacks, and pairs well with dense tables.

### Scale

| Token | Size | Line height | Typical use |
|-------|------|-------------|-------------|
| `font.size.2xs` | 11px | 16px | Meta, dense table secondary |
| `font.size.xs` | 12px | 16px | Captions, badges |
| `font.size.sm` | 13px | 18px | Compact controls, secondary text |
| `font.size.md` | 14px | 20px | Body default |
| `font.size.lg` | 16px | 24px | Emphasized body, form section titles |
| `font.size.xl` | 18px | 28px | Panel titles |
| `font.size.2xl` | 22px | 28px | Page titles |
| `font.size.3xl` | 28px | 36px | Dashboard hero KPI (sparingly) |

### Weights

| Token | Value |
|-------|-------|
| `font.weight.regular` | 400 |
| `font.weight.medium` | 500 |
| `font.weight.semibold` | 600 |
| `font.weight.bold` | 700 |

### Semantic type roles

| Role | Size | Weight | Notes |
|------|------|--------|-------|
| `text.pageTitle` | 2xl | semibold | Object / page header |
| `text.sectionTitle` | lg | semibold | Form / panel sections |
| `text.body` | md | regular | Default |
| `text.label` | sm | medium | Field labels |
| `text.helper` | xs | regular | Helper / error under fields |
| `text.code` | sm | regular | Mono family |

---

## 3. Spacing

Base unit: **4px**.

| Token | px |
|-------|----|
| `space.0` | 0 |
| `space.1` | 4 |
| `space.2` | 8 |
| `space.3` | 12 |
| `space.4` | 16 |
| `space.5` | 20 |
| `space.6` | 24 |
| `space.8` | 32 |
| `space.10` | 40 |
| `space.12` | 48 |
| `space.16` | 64 |
| `space.20` | 80 |

### Layout spacing

| Token | Value | Use |
|-------|-------|-----|
| `layout.page.padding.x` | `space.6` (md+), `space.4` (sm) | Content gutter |
| `layout.page.padding.y` | `space.6` | Vertical page padding |
| `layout.section.gap` | `space.8` | Between major sections |
| `layout.stack.gap` | `space.4` | Default vertical stack |
| `layout.inline.gap` | `space.2` | Chip / button groups |
| `layout.nav.width` | 248px | Expanded left nav |
| `layout.nav.width.collapsed` | 64px | Icon rail |
| `layout.content.max` | 1440px | Soft max for registries / dashboards |
| `layout.object.max` | 1120px | Comfortable Object Page reading width |
| `layout.panel.width` | 360px | Secondary / related panel |

---

## 4. Sizing

### Control heights

| Token | px | Use |
|-------|----|-----|
| `size.control.sm` | 28 | Dense tables, compact toolbars |
| `size.control.md` | 36 | Default inputs / buttons |
| `size.control.lg` | 44 | Touch-primary / mobile CTAs |

### Icon sizes

| Token | px |
|-------|----|
| `size.icon.xs` | 12 |
| `size.icon.sm` | 16 |
| `size.icon.md` | 20 |
| `size.icon.lg` | 24 |
| `size.icon.xl` | 32 |

### Radius

| Token | px | Use |
|-------|----|-----|
| `radius.none` | 0 | Full-bleed / dense grids (rare) |
| `radius.sm` | 4 | Badges, small chips |
| `radius.md` | 8 | Buttons, inputs, cards |
| `radius.lg` | 12 | Panels, dialogs |
| `radius.full` | 9999 | Avatars only — not default for buttons |

### Shadows / elevation

| Token | Intent |
|-------|--------|
| `shadow.none` | Flat surfaces |
| `shadow.xs` | Subtle lift (dropdown edge) |
| `shadow.sm` | Popovers, menus |
| `shadow.md` | Dialogs, drawers |
| `shadow.lg` | Rare — modal stacks |

Prefer border + surface change over heavy multi-layer shadows.

---

## 5. Color — primitive palette

Primitives are theme-agnostic raw values. Components use **semantic** tokens only.

### Brand / primary (deep operational teal)

| Token | Hex | Notes |
|-------|-----|-------|
| `palette.teal.50` | `#E6F4F3` | |
| `palette.teal.100` | `#C5E6E3` | |
| `palette.teal.200` | `#8FCDC8` | |
| `palette.teal.300` | `#56AFA8` | |
| `palette.teal.400` | `#2F8F88` | |
| `palette.teal.500` | `#1B726C` | Primary interactive (light) |
| `palette.teal.600` | `#155A55` | Hover |
| `palette.teal.700` | `#104440` | Active / pressed |
| `palette.teal.800` | `#0B2F2C` | |
| `palette.teal.900` | `#071F1D` | |

### Secondary (slate)

| Token | Hex |
|-------|-----|
| `palette.slate.50`–`900` | `#F5F7F9` … `#0E1418` |

Use slate for neutrals, chrome, and secondary actions.

### Semantic hues

| Family | Anchor | Role |
|--------|--------|------|
| `palette.green.*` | `#1F7A4D` | Success / effective |
| `palette.amber.*` | `#B86E00` | Warning / overdue / partial |
| `palette.red.*` | `#C0352B` | Critical / ineffective / destructive |
| `palette.blue.*` | `#2B6CB0` | Info / in-progress |
| `palette.violet.*` | `#5B4B8A` | Reserved — knowledge / secondary taxonomy only; **not** product chrome |

Full 50–900 ramps for green/amber/red/blue are required at implementation; anchors above define hue intent.

---

## 6. Color — semantic tokens (Light defaults)

| Token | Light mapping | Purpose |
|-------|---------------|---------|
| `color.bg.canvas` | slate.50 | App background |
| `color.bg.surface` | `#FFFFFF` | Cards, panels |
| `color.bg.surfaceRaised` | `#FFFFFF` | Elevated panels |
| `color.bg.subtle` | slate.100 | Striped rows, muted wells |
| `color.bg.inverse` | slate.900 | Inverse chips (rare) |
| `color.border.default` | slate.200 | Dividers, input borders |
| `color.border.strong` | slate.400 | Emphasis borders |
| `color.border.focus` | teal.500 | Focus ring base |
| `color.text.primary` | slate.900 | Body |
| `color.text.secondary` | slate.600 | Supporting |
| `color.text.muted` | slate.500 | Meta |
| `color.text.inverse` | `#FFFFFF` | On primary / inverse |
| `color.text.link` | teal.600 | Links |
| `color.interactive.default` | teal.500 | Primary buttons, key controls |
| `color.interactive.hover` | teal.600 | |
| `color.interactive.active` | teal.700 | |
| `color.interactive.muted` | teal.100 | Selected row / soft highlight |
| `color.disabled.bg` | slate.100 | |
| `color.disabled.text` | slate.400 | |
| `color.disabled.border` | slate.200 | |
| `color.focus.ring` | teal.500 @ 40% | 2px ring + offset |
| `color.selection.bg` | teal.100 | Text / row selection |
| `color.danger.fg` | red.600 | Destructive text |
| `color.danger.bg` | red.50 | |
| `color.success.fg` | green.700 | |
| `color.success.bg` | green.50 | |
| `color.warning.fg` | amber.800 | |
| `color.warning.bg` | amber.50 | |
| `color.info.fg` | blue.700 | |
| `color.info.bg` | blue.50 | |
| `color.critical.fg` | red.700 | Highest severity |
| `color.critical.bg` | red.100 | |

Status-specific semantic tokens are listed in [StatusLanguage.md](StatusLanguage.md).

Dark theme remaps are in [Themes.md](Themes.md).

### Document shelf («Полка», TASK-P11-012 §6)

The shelf content area uses its own palette («Тёплая бумага»). The shell, navigation and
place panel keep the global tokens. Primitives (`primitive.palette`):

| Family | Stops |
|---|---|
| `paper` | 50 `#FFFDF9`, 100 `#F7F4EE`, 150 `#F5F3EC`, 200 `#E4DED2`, 300 `#CFC8BA`, 400 `#B4B0A6`, 500 `#6B665C`, 600 `#4A4740`, 700 `#3A3D38`, 800 `#262925`, 900 `#1F2220` |
| `graphite` | 400 `#6E6E6E`, 600 `#3B3B3B` |
| `forest` | 500 `#417760`, 800 `#213C30` |
| `ochre` | 100 `#F3E3C3`, 200 `#E9D6A8`, 300 `#E0C27E`, 400 `#C9A45E`, 600 `#A47A2C`, 800 `#5A4316`, 900 `#5A3F0E` |
| `brick` | 100 `#EADBD5`, 500 `#CA372D`, 700 `#87251E`, 900 `#342522` |

Semantic tokens (light / dark), consumed as `--sm-color-shelf-*`:

| Token | Light | Dark | Meaning |
|---|---|---|---|
| `shelf-page-bg` | paper.100 | paper.900 | Shelf background |
| `shelf-ink` | paper.500 | paper.400 | Secondary text on the shelf |
| `shelf-card-bg` / `shelf-card-border` | paper.50 / paper.200 | paper.800 / paper.700 | Cards |
| `shelf-plank` | paper.300 | paper.600 | Shelf board |
| `shelf-present-bg` | graphite.600 | graphite.400 | Есть (also its border) |
| `shelf-progress-bg` | forest.800 | forest.500 | В работе (also its border) |
| `shelf-spine-fg` | paper.150 | paper.150 | Text on present / progress spines |
| `shelf-progress-ribbon` | ochre.400 | ochre.300 | Bookmark ribbon |
| `shelf-review-bg` / `-border` / `-fg` | ochre.200 / ochre.400 / ochre.900 | ochre.800 / ochre.600 / ochre.100 | Пересмотр |
| `shelf-missing-border` | brick.700 | brick.500 | Нет (dashed 1.5 px; also text) |
| `shelf-missing-bg` | brick.100 | brick.900 | Tint of an empty place |
| `shelf-clarify-border` | slate.400 | slate.400 | Уточнить (dotted 1.5 px) |
| `shelf-excluded-border` | paper.300 | paper.600 | Исключено (dashed 1 px) |
| `shelf-ack-dot` | brick.700 | brick.500 | Not everyone acquainted |

Contrast pairs are tested in
`frontend/src/features/document-shelf/shelf-tokens-contrast.test.ts`. Graphics must reach
≥ 3:1 on `shelf-page-bg`, and text ≥ 4.5:1. The dark «В работе» is `#417760` instead of the first `#437B62`, which gave only 4.45:1 for spine text (product owner, 2026-11-06).

---

## 7. Z-index scale

| Token | Value | Layer |
|-------|-------|-------|
| `z.base` | 0 | Content |
| `z.sticky` | 100 | Sticky headers / action bars |
| `z.dropdown` | 200 | Menus |
| `z.drawer` | 300 | Side drawers |
| `z.modal` | 400 | Dialogs |
| `z.toast` | 500 | Toasts |
| `z.tooltip` | 600 | Tooltips |

---

## 8. Breakpoints

| Token | Min width |
|-------|-----------|
| `bp.sm` | 640px |
| `bp.md` | 768px |
| `bp.lg` | 1024px |
| `bp.xl` | 1280px |
| `bp.2xl` | 1536px |

See [Responsive.md](Responsive.md).

---

## 9. Delivery format (planned)

When frontend bootstrap lands, tokens ship as:

```text
theme/
  tokens/
    primitive.json   # or .ts
    semantic.light.json
    semantic.dark.json
  css/
    variables.css    # --sm-color-bg-canvas, etc.
```

Prefix recommendation: `--sm-` (SafetyMAIN) to avoid collisions.
