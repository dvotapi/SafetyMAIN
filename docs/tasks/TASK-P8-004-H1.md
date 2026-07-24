# TASK-P8-004-H1 — RiskControl Persistence and API Hardening

Status: Completed  
Date: 2026-07-24

## Goal

Close TASK-P8-004 with PostgreSQL contracts, restart persistence, API e2e coverage,
architecture docs, and an explicit correction-record decision.

## Implementation summary

- Expanded shared `RiskControlRepositoryContractSuite` (in-memory + PostgreSQL).
- Restart persistence with engine dispose/recreate.
- Optimistic concurrency and materialization uniqueness after restart.
- API lifecycle, RBAC, cross-tenant 404, materialization, verification variants.
- Migration schema assertions for `0012_risk_controls`.
- Architecture guardrails for domain/application/API boundaries.
- Documentation updates including correction-record Outcome A.

## Verification results

| Check | Result |
|-------|--------|
| `pytest -m "not db"` | **779 passed**, 133 deselected |
| `pytest -m db -k "risk_control"` | **11 passed** |
| Repository contracts (memory) | `tests/contracts/test_risk_control_repository_contracts.py` |
| PostgreSQL contracts | `tests/contracts/test_sqlalchemy_risk_control_contracts.py` |
| Restart persistence | `tests/infrastructure/test_risk_control_restart_persistence.py` |
| API e2e (in-memory app wiring) | `tests/api/test_risk_controls_api.py` |
| Materialization application | `tests/application/test_risk_control_materialize.py` |
| Architecture guardrails | `tests/architecture/test_p8_risk_control_guardrails.py` |
| Migration schema | `tests/infrastructure/test_risk_control_migration.py` |
| Alembic head | `0012_risk_controls` (single head) |
| Ruff (touched files) | clean |

## Correction-record decision

**Outcome A — Deferred capability**

- Verification history is append-only.
- Source assessment snapshots are immutable after control creation.
- Evidence after `Implemented` requires explicit correction flag.
- Dedicated `CorrectionRecord` model deferred to `TASK-P8-HARDENING-001`.

## Deferred items

- Full dedicated `CorrectionRecord` aggregate (`TASK-P8-HARDENING-001`)
- Dedicated PostgreSQL HTTP e2e suite beyond repository/restart (API uses enforced in-memory wiring matching Hazard/RiskAssessment tests; DB contracts cover persistence)
- Reminder workers / binary evidence storage

## Related docs

- [RiskControl.md](../domain/RiskControl.md)
- [LifecycleRules.md](../domain/LifecycleRules.md)
- [DomainEvents.md](../domain/DomainEvents.md)
- [RiskControlPersistence.md](../architecture/RiskControlPersistence.md)
- [RiskControlsAPI.md](../api/RiskControlsAPI.md)
- [TASK-P8-004.md](TASK-P8-004.md)
