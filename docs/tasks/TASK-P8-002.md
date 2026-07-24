# TASK-P8-002 — Hazard Management Foundation

Status: Implemented

## Outcome

SafetyMAIN now has a complete organization-scoped hazard vertical slice:

Domain → Application → PostgreSQL persistence → REST API → RBAC → Audit.

## Delivered

- Refined `Hazard` aggregate with classifications, lifecycle restore, versioning
- Org-scoped repository contract + in-memory and SQLAlchemy implementations
- Alembic head `0010_safety_hazards`
- Commands/queries for create/update/activate/archive/restore/get/list
- `/api/v1/hazards` endpoints without physical delete
- Permissions, audit taxonomy (`safety.hazard.*`), architecture guardrails
- Contract, API, and domain tests

## Non-goals (still deferred)

Risk assessment, controls, inspections, incidents, SOUT/OPO registries,
ADR engines, Knowledge Engine, UI.
