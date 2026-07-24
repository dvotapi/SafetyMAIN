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
