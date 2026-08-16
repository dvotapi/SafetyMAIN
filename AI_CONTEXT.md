# SafetyMAIN AI Context

## Project purpose

SafetyMAIN is a multi-tenant enterprise safety management platform.

## Repository structure

- `backend/` — backend application and domain logic
- `frontend/` — Next.js frontend
- `docs/architecture/` — architecture decisions and system documentation
- `docs/tasks/` — implementation task specifications, approved plans, and completion reports
- `docs/ai/` — AI-assisted development workflow, prompts, and review guidance
- `tests/` — automated tests where applicable
- `alembic/` or backend migration directories — database migrations
- `infrastructure/production/` — production Docker Compose stack, Dockerfiles, and environment template
- `docs/infrastructure/ApplicationServerDeployment.md` — production deployment runbook

## Mandatory workflow

All implementation work must follow:

- `docs/ai/DevelopmentWorkflow.md`

The workflow is mandatory for human developers and AI agents.

Do not skip planning, review, correction, or acceptance stages unless the user explicitly approves an exception.

## Authoritative sources

Use sources in this order:

1. Current task document in `docs/tasks/`
2. Approved implementation plan inside the current task document
3. Relevant architecture documents in `docs/architecture/`
4. Existing production implementation
5. Existing tests
6. General assumptions only when the repository provides no answer

When sources conflict:

- do not guess;
- identify the conflict;
- prefer the current approved task and architecture;
- request clarification before changing public contracts or architecture.

## Backend principles

- Domain-driven architecture
- Explicit aggregate lifecycle
- Multi-tenant isolation
- SecurityContext and TenantContext
- Role-based authorization
- Audit event taxonomy
- PostgreSQL persistence
- Alembic migrations
- No destructive DELETE endpoints unless explicitly designed
- Cross-organization resources must use 404 masking
- Backend contracts are authoritative for lifecycle, validation, permissions, and calculated results
- Do not invent endpoints, permissions, transitions, or DTO fields

## Frontend principles

- Next.js and React
- Strict TypeScript
- Shared components imported from `@/components`
- Feature code must depend on shared layers, not the reverse
- Features must not import another feature's internal modules
- Cross-feature navigation should use public routes or explicitly approved public boundaries
- Use the established design system
- Preserve authentication and organization context
- Permissions must be derived from capabilities, not hard-coded roles
- Do not duplicate backend-authoritative calculations in the frontend
- Do not add unsupported filters, sorting, or actions

## Task workflow

For every task:

1. Read `docs/ai/DevelopmentWorkflow.md`.
2. Read the current task specification.
3. Read the approved implementation plan, if present.
4. Locate directly related architecture documentation.
5. Find the nearest completed vertical slice.
6. Inspect only files relevant to the current phase.
7. Plan before editing.
8. Implement one approved phase at a time.
9. Run focused tests first.
10. Perform self-review.
11. Request independent review.
12. Fix only confirmed review findings.
13. Do not start the next phase without explicit approval.
14. Update documentation and the task completion report when required.

## Phase boundaries

One chat should cover one logical phase.

Recommended separation:

- architecture;
- task specification;
- implementation planning;
- plan review;
- one implementation phase;
- independent review;
- correction pass;
- task completion.

Do not continue into the next phase automatically.

## Implementation constraints

Before modifying files, confirm:

- the task exists;
- the current phase is identified;
- the implementation plan is approved;
- the scope and non-goals are clear;
- relevant contracts have been inspected.

During implementation:

- make the smallest correct change;
- do not refactor unrelated code;
- do not add speculative abstractions;
- do not implement future phases;
- do not silently change public API contracts;
- do not weaken authentication, authorization, tenant isolation, audit, or validation;
- do not bypass failing tests.

## Phase completion

A phase must not be declared complete until:

- implementation matches the approved phase;
- no unrelated changes were introduced;
- focused tests pass;
- type checking passes where applicable;
- self-review is complete;
- no known BLOCKER or IMPORTANT findings remain unresolved;
- the independent review decision allows acceptance.

Valid review decisions:

- `APPROVE`
- `APPROVE WITH MINOR CORRECTIONS`
- `REJECT — CORRECTIONS REQUIRED`

A rejected phase must not proceed to the next phase.

## Communication

- Tasks, code, comments, identifiers, technical documentation, and Cursor instructions must be written in English.
- Explanations to the user must be written in Russian.
- Report uncertainty honestly.
- Distinguish confirmed repository facts from assumptions.
- Always report:
  - files changed;
  - tests and checks executed;
  - exact results;
  - unresolved questions;
  - deviations from the approved plan.

## Context discipline

Do not load all project documentation automatically.

Search for and read only documents relevant to the current task and current phase.

Do not scan the entire repository unless explicitly required.

Do not repeatedly read unchanged files already inspected in the current phase.

Prefer targeted searches by:

- task ID;
- aggregate or feature name;
- route;
- API endpoint;
- DTO or schema;
- permission;
- repository;
- test name.

## Important

Architecture is decided before implementation.

Implementation proceeds only from an approved task and approved plan.

Each implementation phase requires review and explicit acceptance before the next phase begins.