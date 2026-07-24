# Frontend Architecture (Runtime)

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-002

Related:

- [Design System](../../design/README.md)
- [Design FrontendArchitecture](../../design/FrontendArchitecture.md)
- [ADR-FrontendUILibrary.md](ADR-FrontendUILibrary.md)
- [FrontendTheming.md](FrontendTheming.md)
- [FrontendTesting.md](FrontendTesting.md)

---

## Location

Application lives in `frontend/` (repository convention). Not `apps/web/` — no monorepo tool required yet.

## Stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js 15 App Router |
| UI | React 19 |
| Language | TypeScript strict |
| Tokens | JSON source → generated CSS + TS |
| Icons | Lucide React (outline) |
| Server state | TanStack Query (provider only) |
| Forms | React Hook Form + Zod (adapter demo) |
| UI primitives | Custom + Radix Slot |

## Source layout

```text
frontend/src/
  app/           # routes, providers, globals
  components/    # primitives, patterns, feedback
  layouts/       # AppShell
  features/      # business modules (empty placeholder)
  services/      # api, auth extension points
  theme/         # tokens source + generated + providers
  icons/
  lib/           # env, navigation model
  hooks/
  types/
  utils/
  test/
```

## Dependency direction

```text
app → features → components/layouts → theme/utils/icons
```

Forbidden:

- `components` → `features`
- `theme` → `features`
- `features` → `app`

Enforced by ESLint `import/no-restricted-paths` and `dependency-cruiser` (`npm run architecture:check`).

## Server / client boundaries

- Server Components by default.
- `"use client"` only for interactive shell, theme, forms, providers.
- Secrets never via `NEXT_PUBLIC_*`.
- `server-only` available for future server modules; do not import into client components.

## API client

`services/api` provides typed fetch wrapper, Bearer/org header extension points, correlation id, and normalized errors (`ValidationError`, `ConflictError`, …). No business endpoints in P9-002.

## Environment

Validated public env via Zod (`src/lib/env.ts`). See `frontend/.env.example`.
