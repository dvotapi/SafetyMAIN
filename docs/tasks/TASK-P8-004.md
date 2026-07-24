# TASK-P8-004 — Risk Controls and Control Effectiveness

Status: **Completed** (closed by TASK-P8-004-H1)  
Date: 2026-07-24

## Deliverables

- Domain aggregate `RiskControl` with full lifecycle
- Materialization from approved risk assessments
- PostgreSQL persistence + Alembic `0012_risk_controls`
- Application commands/queries/handlers
- REST API `/api/v1/risk-controls`
- RBAC `risk_control:*`, audit `safety.risk_control.*`
- Contract/domain/API/architecture tests and docs

## Hardening (H1)

See [TASK-P8-004-H1.md](TASK-P8-004-H1.md) for PostgreSQL contracts, restart persistence,
API e2e coverage, and the correction-record decision (**Outcome A — deferred**).

## Non-goals (remain deferred)

Full inspection/incident/corrective/training stacks, binary evidence storage,
auto residual-risk mutation, UI, schedulers, dedicated CorrectionRecord model.
