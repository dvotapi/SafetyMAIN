# TASK-P2-001

## Title

Bootstrap FastAPI Application Foundation

## Goal

Create the HTTP API foundation for SafetyMAIN using FastAPI.

The application shall provide:

- an explicit application factory;
- versioned API routing;
- health and readiness endpoints;
- request-scoped SQLAlchemy Unit of Work creation;
- centralized exception handling;
- consistent API error responses;
- environment-based configuration;
- foundational HTTP tests.

Do not implement Knowledge Object or Relation business endpoints in this task.

## Acceptance Criteria

- FastAPI application factory exists.
- API is versioned under `/api/v1`.
- Health endpoint returns process health without database access.
- Readiness endpoint supports a minimal injectable database check.
- Request-scoped Unit of Work dependency exists.
- Unit of Work is not committed automatically by the HTTP dependency.
- Centralized typed exception handlers exist.
- Validation errors use the common API error schema.
- Unexpected errors return a safe generic response.
- Every response includes `X-Request-ID`.
- Application creation has no external database side effects.
- Tests can replace infrastructure dependencies.
- API tests run without PostgreSQL.
- Domain and Application remain independent of FastAPI.
- Architecture tests protect the new dependency boundary.
- API foundation documentation exists.
- Existing Domain, Application, persistence and contract tests remain passing.
- Ruff passes.
- Import validation passes.
- IDE diagnostics are clean.
