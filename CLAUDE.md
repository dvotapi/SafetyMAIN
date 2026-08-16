# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Mandatory workflow — read this first

This repository enforces a strict, phase-gated AI workflow defined in `AI_CONTEXT.md`, `docs/ai/DevelopmentWorkflow.md`, and `.cursor/rules/*.mdc`. It applies to every AI agent, including Claude Code. Key rules:

- **Pull before any changes.** Before editing files, committing, or starting planning/implementation, run `git pull` (or `git pull --rebase` if that is the local convention) so the working tree matches `origin`. Do not invent commits on a stale branch. If pull reports conflicts or diverged history, stop and resolve with the user before continuing.
- **Authority order** when sources conflict: current TASK document (`docs/tasks/TASK-*.md`) → approved implementation plan → `docs/architecture/*` → existing production implementation → existing tests → general assumptions (only if nothing else answers it). Never guess; surface the conflict and ask.
- **Never begin implementation without an approved plan.** Planning (investigation only, no code) and implementation are separate phases. Do not implement future phases speculatively.
- **Smallest correct change.** No unrelated refactors, no speculative abstractions, no scope creep. Every change must trace back to a TASK or an approved plan.
- **Backend is authoritative.** Never invent API endpoints, permissions, lifecycle transitions, DTO fields, filters, sorting, or calculations on the frontend. Never duplicate backend-authoritative calculations in the frontend.
- **Never weaken** authentication, authorization, tenant isolation, audit, validation, or optimistic concurrency. Never expose data across organizations (cross-tenant access must present as 404, not 403).
- **Context discipline:** read `AI_CONTEXT.md`, the current task doc, and only directly relevant architecture docs — don't scan the whole repo. Prefer targeted search by task ID, aggregate/feature name, route, DTO, permission, or test name.
- **Communication:** code, comments, identifiers, commit messages, and technical docs must be in English. Explanations to the user must be in Russian (per user's global instructions, always respond in Russian regardless).

Full review/planning/implementation checklists live in `.cursor/rules/10-review-behavior.mdc`, `20-planning-behavior.mdc`, `30-implementation-behavior.mdc` — read them before doing review, planning, or implementation work respectively.

## What SafetyMAIN is

An AI-native Enterprise Compliance Operating System (ECOS) for occupational/industrial/fire/road/environmental safety management. Governed by `docs/architecture/ArchitectureConstitution.md` — its core tenets:

- **Knowledge First**: everything is a Knowledge Object; documents are generated evidence, not the source of truth.
- **Entity-Centric Architecture** (`docs/architecture/ADR-0001-Entity-Centric-Architecture.md`): every business object (Hazard, Risk, Organization, Employee, Document, ...) is an Entity sharing the same core capabilities (UUID, versioning, audit, metadata, relations, tags, permissions, org ownership). Do not create isolated business objects outside this model without an ADR.
- **Metadata describes the business; rules describe behavior**; business workflows must not be hardcoded.
- **Organization is the tenant boundary** for every Knowledge Object.

## Commands

### Backend (Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL)

```bash
python -m pip install -e ".[dev]"        # install
python -m pytest                          # full suite (functional + architecture tests)
python -m pytest tests/api/test_hazards_api.py::test_name  # single test
python -m pytest -m db                    # PostgreSQL-backed tests (see below)
python -m ruff check .                    # lint
python -m alembic upgrade head            # apply migrations
python -m alembic revision -m "..." --autogenerate  # new migration
docker compose up -d                      # local Postgres (safetymain/safetymain@localhost:5432/safetymain)
```

Tests marked `db` are skipped unless `SAFETYMAIN_RUN_DB_TESTS=1` **and** `DATABASE_URL` is set and reachable — otherwise `tests/infrastructure/db_fixtures.py` fails loudly rather than silently skipping. CI (`.github/workflows/postgresql-tests.yml`) runs migrations then `pytest -m db` against a real Postgres 17 service, and asserts zero DB tests were skipped.

### Frontend (`frontend/`, Next.js 15 App Router, React 19, strict TypeScript)

```bash
cd frontend && nvm use && npm ci && npm run tokens:build && npm run dev  # http://localhost:3100
npm run lint                 # ESLint, --max-warnings=0
npm run typecheck            # tsc --noEmit
npm run test                 # Vitest
npm run test:e2e             # Playwright (needs build+start or running server)
npm run architecture:check   # dependency-cruiser boundary checks
npm run verify                # tokens → format:check → lint → typecheck → architecture:check → test → build (run before considering frontend work done)
```

### Production deployment (`infrastructure/production/`)

```bash
cd infrastructure/production && cp .env.example .env   # server-side only, never committed
docker compose --profile migrate run --rm migrate      # alembic upgrade head
docker compose up -d                                   # safetymain-backend + safetymain-frontend
```

Application-only Compose stack (no PostgreSQL — the database lives on a separate server), fronted by the host's existing reverse proxy with frontend and API on one public origin. Runbook: `docs/infrastructure/ApplicationServerDeployment.md`. First admin on an empty production database: `scripts/bootstrap_admin.py` (one-shot; refuses when any user exists).

## Backend architecture

Clean Architecture layering under `backend/core/`, enforced by pytest architecture tests (`tests/architecture/`, rules documented in `docs/architecture/ArchitectureTesting.md`):

- `domain/` — entities, value objects, domain events, domain exceptions, repository interfaces. May depend only on the stdlib, Pydantic, and itself. **Must not** import `application` or `infrastructure`, or any framework/storage library (FastAPI, SQLAlchemy, Redis, MinIO).
- `application/` — use-case handlers (`handlers/`), commands, queries, DTOs, authorization/tenant services. Depends on `domain` and `contracts` only, never on `infrastructure`.
- `contracts/` — ports (interfaces) that infrastructure implements (e.g. `unit_of_work.py`, `token_service.py`, `password_hasher.py`). Must stay independent of concrete adapters.
- `infrastructure/` — SQLAlchemy/in-memory persistence, auth (JWT, bcrypt), messaging, storage, search, time. Implements `contracts/` ports; depends inward on domain/application/contracts.
- `capabilities/`, `knowledge/`, `shared/`, `kernel/`, `services/`, `storage/`, `exceptions/` — supporting/cross-cutting modules.

`backend/api/` is the FastAPI HTTP boundary: `app.py` composes routers under `backend/api/routers/` (one router per aggregate: hazards, risk_assessments, risk_controls, knowledge_objects, relations, auth, invitations, admin_*). `create_app()` never connects to the DB or applies migrations on import — dependency wiring happens in `backend/bootstrap/container.py` (`AppContainer`, an explicit composition root, not a service locator), with settings loaded via `backend/bootstrap/settings.py` and validated by `backend/bootstrap/security_validation.py`.

Persistence uses the Unit-of-Work pattern (`UnitOfWorkContract`, `SQLAlchemyUnitOfWork` / `InMemoryUnitOfWork`), swappable per environment — production always requires PostgreSQL and refuses in-memory identity/membership stores.

Aggregates currently implemented: Organization, Membership, Invitation, User (identity), RefreshTokenSession, AuditEvent, KnowledgeObject + KnowledgeObjectRelation, Hazard, Risk, RiskAssessment, RiskControl, Incident, Inspection, CorrectiveAction, Training/Permit/EmergencyAsset. Alembic migrations live in `alembic/versions/`, one migration per schema change, named sequentially.

Security model: JWT bearer auth (`AUTH_ENFORCEMENT` toggles enforced vs. compatibility mode), `SecurityContext`/`TenantContext` on every request, role-based authorization via `AuthorizationService`, and an integrity-chained audit event log (`docs/architecture/AuditEventIntegrity.md`) — every audit event is hash-chained to detect tampering (`scripts/verify_audit_integrity.py` / `tests/infrastructure/test_audit_integrity_*`). Cross-organization access to a resource must return 404, never 403 or leaked data.

## Frontend architecture

Boundaries are enforced by `frontend/.dependency-cruiser.cjs`, not just convention:

- `components/*` (shared Design System) must never import `features/*`; `theme/*` must never import `features/*`.
- `features/*` must never import `app/*` route internals, and must never import another feature's internals directly (only that feature's `index.ts` public export).
- Feature `api/` modules (e.g. `features/hazards/api`, `risk-control-api-no-components`) must not import React components; feature presentation code must not import the raw API client directly (e.g. `risk-control-presentation-no-fetch`).

Structure: `app/` (Next.js routes) · `components/` (shared, domain-agnostic UI) · `layouts/` · `features/<domain>/{pages,components,hooks,api,index.ts}` (hazards, risk-assessments, risk-controls, auth, ...) · `hooks/`, `services/`, `theme/` (design tokens — no hardcoded hex outside `theme/`), `icons/`, `utils/`. Full rules in `docs/design/FrontendArchitecture.md`.

The registry list pattern (filter bar, data grid, bulk command bar, pagination) used for Hazards/Risk Assessments/Risk Controls/Users/Audit events is documented in `docs/design/RegistryPattern.md` — reuse it rather than building new list UIs from scratch. Broader design system reference: `docs/design/README.md` and `docs/architecture/frontend/`.

## Key documentation map

- `AI_CONTEXT.md` — always read before non-trivial work.
- `docs/architecture/` — ADRs, constitution, per-domain architecture (identity, audit, hazards, risk assessment/control, authorization, security).
- `docs/domain/` — ubiquitous language, aggregates, domain events, lifecycle rules.
- `docs/api/` — one doc per REST resource (source of truth for endpoints/DTOs alongside the actual router/schema code).
- `docs/design/` — frontend design system (tokens, components, patterns, accessibility).
- `docs/infrastructure/ApplicationServerDeployment.md` — production deployment runbook (Compose stack, reverse proxy, migrations, identity bootstrap, rollback).
- `docs/tasks/` and `blueprint/tasks/` — task specs and implementation plans; the authoritative contract for any given piece of work.

## Keeping this file current

This file is the AI agent's entry point to the repository — it must stay accurate. After completing a task that changes architecture, workflow rules, commands, directory structure, or conventions described above, update the relevant section of this file in the same change. Do not wait to be asked. Keep additions as terse as the rest of the file; do not restate what's already discoverable from code or docs.

## Общайся на русском и держи файлы CLAUDE.md и AI_CONTEXT.md актуальными

## Caveman skill

Always use caveman skill/mode for all responses in this repo.