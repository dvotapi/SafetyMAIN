# Architecture Testing

SafetyMAIN Core uses pytest-based architecture tests to protect Clean Architecture boundaries.

## Allowed Dependencies

- `domain` may depend on the standard library, Pydantic, and `backend.core.domain`.
- `application` may depend on `backend.core.domain`, `backend.core.contracts`, and application-local modules.
- `infrastructure` may depend inward on domain, application, and contracts.
- `contracts` must remain independent from concrete infrastructure adapters.

## Forbidden Dependencies

- `domain` must not import `backend.core.application` or `backend.core.infrastructure`.
- `application` must not import `backend.core.infrastructure`.
- `contracts` must not import `backend.core.infrastructure`.
- Core layers must not import framework or storage libraries such as FastAPI, SQLAlchemy, Redis, or MinIO unless explicitly allowed by a future architecture decision.

## Running Checks

Run all functional and architecture tests:

```bash
python3 -m pytest
```

Run lint checks:

```bash
python3 -m ruff check .
```

## Interpreting Failures

Architecture test failures include the source file, forbidden import, and violated rule. Fix the dependency direction by moving abstractions inward, depending on contracts, or relocating infrastructure-specific code to the infrastructure layer.
