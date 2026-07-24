# Iconography

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Tokens.md](Tokens.md) · [StatusLanguage.md](StatusLanguage.md) · [Navigation.md](Navigation.md)

---

## 1. Style

| Attribute | Rule |
|-----------|------|
| Style | Outline / stroke icons (not filled as default) |
| Grid | 24×24 optical grid; export at 24px base |
| Stroke | 1.75px at 24px (≈1.5–2px optical) |
| Caps | Rounded |
| Corners | Rounded joins |
| Fill | Use filled variants only for selected nav / active status accents |
| Library | Lucide-compatible set (or equivalent outline set with same metrics) |

Do not mix icon families within the product chrome.

## 2. Sizing

Use `size.icon.*` tokens only:

| Context | Token |
|---------|-------|
| Inline with body text | `sm` (16) |
| Buttons, inputs, table actions | `md` (20) |
| Navigation items | `md` (20) |
| Empty states / page illustrations | `xl` (32) or larger illustration, not icon spam |

Icons inherit `currentColor` unless a status token explicitly overrides.

## 3. Usage rules

1. Pair critical statuses with icon **and** text label.
2. Decorative icons: `aria-hidden="true"`.
3. Icon-only buttons require accessible names.
4. Do not use emoji as product iconography.
5. Keep stroke weight consistent when swapping icons.

## 4. Domain concept map

Canonical icons for primary concepts (names are Lucide-oriented; implementation may alias):

| Concept | Icon key | Notes |
|---------|----------|-------|
| Hazard | `triangle-alert` | Hazard identification |
| Risk / Risk Assessment | `gauge` | Assessment / rating |
| Control / Risk Control | `shield-check` | Controls & effectiveness |
| Inspection | `clipboard-check` | Planned inspections |
| Finding | `search-check` | Inspection findings |
| Incident | `siren` | Reactive events |
| Training | `graduation-cap` | Competence / courses |
| Knowledge | `book-open` | Knowledge objects |
| Reports / Analytics | `chart-column` | Dashboards & reports |
| Administration | `settings` | Tenant admin |
| People / Employee | `users` | People section |
| Overview / Home | `layout-dashboard` | Landing |
| Overdue | `clock-alert` | Temporal risk |
| Attachment | `paperclip` | Evidence refs |
| Audit / Timeline | `history` | History events |
| Comment | `message-square` | User commentary |
| Related link | `link-2` | Object relationships |
| Filter | `list-filter` | Registries |
| More actions | `ellipsis` | Overflow menus |

## 5. Navigation icons

Primary nav items always show icon + label at expanded width; icon-only with tooltip when collapsed.

## 6. Status icons

See [StatusLanguage.md](StatusLanguage.md) for per-status icon assignment. Status icons are secondary to the badge label; never replace the label with icon alone in registries.
