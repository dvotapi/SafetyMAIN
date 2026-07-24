# TASK-P9-002 — Frontend Application Bootstrap

Status: **Completed**  
Date: 2026-07-25

## Goal

Convert the Design System (`TASK-P9-001`) into an executable Next.js frontend platform
without business screens.

## Implementation summary

| Item | Result |
|------|--------|
| Location | `frontend/` (existing repo convention; no monorepo tool) |
| Framework | Next.js **15.3.5**, React **19**, TypeScript strict (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, …) |
| Package manager | **npm** (single `package-lock.json`) |
| Node | **20.11.1** (`.nvmrc`); engines `>=20.11.0` |
| Default port | **3100** (avoids local conflicts with other apps on 3000) |
| UI strategy | Custom primitives + Radix Slot + Lucide ([ADR](../architecture/frontend/ADR-FrontendUILibrary.md)) |
| Tokens | Canonical `src/theme/tokens/tokens.json` → `npm run tokens:build` / `tokens:check` |
| Themes | `system` / `light` / `dark` with localStorage + anti-flash script |
| Typography | IBM Plex Sans / Mono via `next/font` |
| Shell | Top bar, left nav, main, theme control, org/user placeholders, skip link |
| Navigation | Typed `primaryNavigation` (Overview → Administration + Safety nested) |
| Page composition | PageContainer, PageHeader, PageSection, PageActions, ContentGrid, SplitLayout |
| API client | `services/api` — Bearer/org hooks, correlation id, normalized errors |
| State | TanStack Query provider; RHF + Zod demo form adapter |
| Storybook | `@storybook/react-vite` 8.6.x (theme + a11y addons) |
| Tests | Vitest (9) + Playwright smoke (1) |
| Guardrails | ESLint restricted paths + dependency-cruiser |
| Verify | `npm run verify` |

## Shared primitives

Button, IconButton, Text, Heading, Link, Badge, StatusBadge, Card, Panel, Divider, Spinner, Skeleton, Alert.

## Verification results

| Check | Result |
|-------|--------|
| `npm run tokens:check` | pass |
| `npm run format:check` | pass |
| `npm run lint` | pass |
| `npm run typecheck` | pass |
| `npm run architecture:check` | pass (0 violations) |
| `npm run test` | **9 passed** |
| `npm run build` | pass |
| `npm run verify` | pass |
| `npm run test:e2e` | **1 passed** (shell, theme, nav) |
| `npm run build-storybook` | pass |

## Known limitations

- Next.js 15.3.5 reports a known upstream advisory; upgrade in a follow-up dependency task.
- Node 20.11.1 emits engine warnings for some Storybook transitive packages preferring ≥20.17.
- Automated axe coverage is bootstrap-only (not a formal WCAG audit).
- StatusBadge icons use Lucide; full domain icon map expands in P9-003.
- MSW handlers are test/dev stubs only.

## Deferred

- Real authentication / refresh tokens / org switching / RBAC nav  
- Business screens (Hazard, RA, Control, …)  
- Full component catalog / Object Page / Registry / Dashboard / Workflow  
- OpenAPI SDK generation  
- i18n, offline, production observability  

## Recommended next tasks

1. **TASK-P9-003** — Shared UI Component Foundation  
2. **TASK-P9-004** — Authentication and Application Shell  
3. **TASK-P9-005** — Frontend API Integration Foundation  

## Docs

- [frontend/README.md](../../frontend/README.md)
- [FrontendArchitecture.md](../architecture/frontend/FrontendArchitecture.md)
- [ADR-FrontendUILibrary.md](../architecture/frontend/ADR-FrontendUILibrary.md)
- [FrontendTheming.md](../architecture/frontend/FrontendTheming.md)
- [FrontendTesting.md](../architecture/frontend/FrontendTesting.md)
- [Design System](../design/README.md)
