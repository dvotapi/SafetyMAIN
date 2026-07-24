# Frontend Architecture

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [README.md](README.md) · [ComponentCatalog.md](ComponentCatalog.md) · [ArchitectureConstitution.md](../architecture/ArchitectureConstitution.md)

---

## 1. Purpose

Define the UI codebase shape so future apps (e.g. Next.js) implement the Design System without reinventing boundaries.

P9-001 documents structure only — **no application code** in this task.

## 2. Recommended structure

```text
app/                 # routes / next app router (or equivalent)
components/          # shared Design System components only
  ui/                # primitives (Button, Dialog, …)
  patterns/          # Timeline, WorkflowStepper, DataGrid chrome, …
layouts/             # Application shell, page frames
pages/               # optional page compositions if not using app router only
features/            # business modules (hazards, risk-controls, …)
  hazards/
  risk-assessments/
  risk-controls/
  …
hooks/               # shared non-business hooks
services/            # app services (auth session helpers, etc.)
api/                 # API clients / DTO mappers
theme/               # tokens, CSS variables, theme providers
icons/               # icon registry wrapping the icon set
utils/               # pure helpers
```

Exact tooling (Next.js, Vite, etc.) is chosen in a later bootstrap task; folders above are normative intent.

## 3. Dependency rules

```text
features/*  →  components/*, layouts/*, theme/*, api/*, hooks/*, icons/*, utils/*
components/*  →  theme/*, icons/*, utils/*   ✅
components/*  →  features/*                 ❌ FORBIDDEN
layouts/*     →  components/*, theme/*      ✅
features/a    →  features/b                 ⚠ avoid; prefer api + shared types
```

| Rule | Rationale |
|------|-----------|
| Shared UI has zero domain feature imports | Prevents coupling and circular design drift |
| Features own business screens & widgets | Domain-specific composition lives here |
| Tokens only via `theme` | No hex in features/components |
| API types may be shared | Visual components still stay domain-agnostic |

## 4. Feature module shape

```text
features/risk-controls/
  pages/           # Registry, Object Page routes
  components/      # feature-local composites
  hooks/
  api/             # or import from root api/
  index.ts         # public exports
```

Feature-local components may wrap shared `StatusBadge` with risk-control status maps — mapping tables live in feature or a shared `status` adapter, not inside primitive Badge.

## 5. Auth, RBAC, tenant

- Shell reads session + TenantContext.
- Features hide nav/actions by permission; never rely on UI alone for security.
- Cross-tenant errors present as Not Found per platform rules.

## 6. Testing architecture (planned)

| Layer | Focus |
|-------|-------|
| Component | a11y, tokens, variants |
| Pattern | Registry keyboard, stepper states |
| Feature | Workflow + API mappers |
| e2e | Critical paths against backend |

## 7. Relationship to backend

UI workflows mirror domain commands (Plan, Verify…) — not generic PATCH-everything forms when dedicated endpoints exist (see Risk Controls API).
