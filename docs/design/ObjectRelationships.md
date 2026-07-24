# Object Relationships

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [PageTemplates.md](PageTemplates.md) · [UbiquitousLanguage.md](../domain/UbiquitousLanguage.md)

---

## 1. Intent

Users navigate the safety value chain without hunting through unrelated registries.

```text
Hazard
  → Risk Assessment
    → Risk Control (materialized)
      → Inspection (planned)
        → Finding (planned)
```

Incidents may link back to hazards/controls without implying a single linear path.

## 2. Visual patterns

| Pattern | Use |
|---------|-----|
| **Related rail** | Side list of typed links on Object Page |
| **Relationship chips** | Compact parent/child references in Summary |
| **Chain breadcrumb** (optional) | Contextual trail when deep-linking from parent |
| **Graph preview** (future) | Not required for P9-001 |

## 3. Link presentation

Each related item shows:

- Type icon ([Iconography](Iconography.md))
- Code + title
- `StatusBadge`
- Optional relationship label (`Materialized from`, `Controls`, `Parent hazard`)

## 4. Rules

1. Links respect RBAC and tenant isolation (404-safe).
2. Do not mutate parent from child views except via explicit domain commands (e.g. materialize).
3. Materialization entry points live on Assessment Object Page actions — not buried only in Control create.
4. Broken / inaccessible links show “Unavailable” without leaking existence across tenants.

## 5. Component

`RelatedObjectsList` with grouped sections by relationship type.
