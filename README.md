# SafetyMAIN

AI-powered Safety Management Platform for Occupational Safety, Industrial Safety, Fire Safety, Road Safety, Environmental Compliance, and related domains.

## Purpose

SafetyMAIN is designed as a modular, metadata-driven platform for managing enterprise safety knowledge, regulatory requirements, documents, training, tasks, and AI-assisted compliance workflows.

## Repository Structure

- `.github/workflows/` - CI/CD workflow definitions.
- `docs/` - architecture, domain model, API, database, AI, and decision records.
- `blueprint/` - planning artifacts: tasks, epics, and sprints.
- `backend/` - backend application source code.
- `frontend/` - frontend application source code.
- `ai/` - AI agents, prompts, models, and knowledge processing components.
- `infrastructure/` - deployment, environment, and infrastructure definitions.
- `scripts/` - automation and maintenance scripts.
- `tests/` - test suites and testing utilities.
- `tools/` - developer and operational tooling.

## Status

Foundation repository structure initialized.

## Security Configuration

Security settings are validated at startup. Development defaults are allowed when
`APP_ENV=development`. Production deployments must configure a strong JWT secret,
issuer, database URL, and `AUTH_ENFORCEMENT=true`.

See [ProductionSecurityConfiguration.md](docs/architecture/ProductionSecurityConfiguration.md).
