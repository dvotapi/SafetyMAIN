# Component Catalog

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [Tokens.md](Tokens.md) · [Forms.md](Forms.md) · [RegistryPattern.md](RegistryPattern.md)

---

## 1. Rules

1. Components live in shared UI; **features depend on components**, never the reverse.
2. Components consume tokens only.
3. Business copy/icons may be passed in as props; domain imports are forbidden inside shared UI.
4. This catalog is the **design contract**. React implementation is a later task.

Status legend for this doc:

| Tag | Meaning |
|-----|---------|
| **Specified** | Design-complete in P9-001 |
| **Deferred code** | Not implemented in repo yet |

All entries below are design contracts. Runtime implementation: **TASK-P9-003** (`@/components`).

---

## 2. Catalog

### Actions

| Component | Responsibility |
|-----------|----------------|
| `Button` | Primary / secondary / ghost / danger; sizes sm/md/lg |
| `IconButton` | Icon-only; requires accessible name |
| `CommandBar` | Sticky group of actions + overflow |

### Status & metadata

| Component | Responsibility |
|-----------|----------------|
| `Badge` | Neutral count / label |
| `StatusBadge` | Lifecycle / operational status ([StatusLanguage](StatusLanguage.md)) |
| `Chip` / `Tag` | Filters, facets, removable selections |
| `Avatar` | User / system actor |

### Surfaces

| Component | Responsibility |
|-----------|----------------|
| `Card` | Interactive or KPI container only — not decorative wrapping |
| `Panel` | Section surface with header |
| `Alert` | Inline page/form feedback |
| `Notification` / `Toast` | Transient feedback |
| `EmptyState` | No data / no results / no access |
| `Skeleton` | Loading placeholders |
| `Progress` | Determinate / indeterminate |

### Data display

| Component | Responsibility |
|-----------|----------------|
| `Table` | Simple read-only tables |
| `DataGrid` | Registry-grade grid (sort, select, density) |
| `PropertyGrid` / `DescriptionList` | Label–value object summaries |
| `Tabs` | Object Page sections |
| `Accordion` | Progressive disclosure blocks |
| `Tree` | Hierarchical org / location (future) |

### Navigation & wayfinding

| Component | Responsibility |
|-----------|----------------|
| `Breadcrumb` | Hierarchy path |
| `SearchBox` | Global or local search |
| `FilterBar` | Registry facets + search |

### Overlays

| Component | Responsibility |
|-----------|----------------|
| `Dialog` | Modal confirm / small form |
| `Drawer` | Side overlay forms / detail |

### Inputs

| Component | Responsibility |
|-----------|----------------|
| `TextField`, `TextArea`, `Select`, `Checkbox`, `Radio`, `Switch` | Standard fields |
| `DatePicker` | Date / date-time with timezone clarity (UTC display rules TBD at impl) |
| `FileReferenceInput` | Evidence **references** — not binary vault in P9 |

### Domain-pattern composites

| Component | Responsibility |
|-----------|----------------|
| `Timeline` / `TimelineItem` | Object history |
| `ActivityFeed` / `ActivityItem` | Streams |
| `WorkflowStepper` | Lifecycle stages |
| `RelatedObjectsList` | Typed links between aggregates |
| `KpiCard` | Dashboard metric |
| `PageHeader` | Title, status, actions |
| `ObjectSummaryStrip` | Key fields under header |

---

## 3. Variant conventions

- **Size:** `sm` | `md` | `lg` mapped to control height tokens.
- **Tone:** `neutral` | `primary` | `success` | `warning` | `danger` | `info`.
- **StatusBadge** uses status tokens, not generic tone alone.

## 4. Do not invent

If a screen needs a new composite, prefer composing catalog items. New primitives require Design System update.
