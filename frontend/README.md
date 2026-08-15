# SafetyMAIN Frontend

Location: `frontend/` — chosen because the repository already reserved this path
for the web application (see root README). No monorepo framework was introduced.

## Runtime

| Item            | Value                                                    |
| --------------- | -------------------------------------------------------- |
| Node.js         | `20.11.1` (see `.nvmrc`)                                 |
| Package manager | npm (single lockfile: `package-lock.json`)               |
| Framework       | Next.js 15 (App Router) + React 19 + TypeScript (strict) |

## Setup

```bash
cd frontend
nvm use   # or install Node 20.11+
cp .env.example .env
npm ci
npm run tokens:build
npm run dev
```

Open http://localhost:3100

## Commands

| Command                                 | Purpose                                                          |
| --------------------------------------- | ---------------------------------------------------------------- |
| `npm run dev`                           | Development server                                               |
| `npm run build` / `npm run start`       | Production build & serve                                         |
| `npm run tokens:build` / `tokens:check` | Generate / verify design tokens                                  |
| `npm run lint`                          | ESLint                                                           |
| `npm run format:check`                  | Prettier                                                         |
| `npm run typecheck`                     | `tsc --noEmit`                                                   |
| `npm run test`                          | Vitest unit/component tests                                      |
| `npm run test:e2e`                      | Playwright smoke (expects build+start or running server)         |
| `npm run storybook`                     | Component workspace                                              |
| `npm run architecture:check`            | dependency-cruiser guardrails                                    |
| `npm run verify`                        | tokens → format → lint → typecheck → architecture → test → build |

Prefer importing from `@/components`. Shared library docs:
[SharedUIComponents.md](../docs/architecture/frontend/SharedUIComponents.md).

Design System source of truth: [docs/design/README.md](../docs/design/README.md).

## Deferred

Authentication, org switching, permission-aware nav, business screens —
see `docs/tasks/TASK-P9-003.md` and follow-ups P9-004 / P9-005.
