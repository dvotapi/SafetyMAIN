# TASK-S1-005

## Title

Introduce Architecture Dependency Tests

## Goal

Add automated tests that protect the Clean Architecture boundaries of SafetyMAIN Core.

The tests shall detect forbidden imports between architectural layers.

This task must not add new business functionality.

## Architectural Rules

Enforce the following dependency rules:

### Domain Layer

`backend/core/domain/` may import:

- Python standard library
- approved third-party domain libraries such as Pydantic
- modules inside `backend.core.domain`
- explicitly shared kernel modules that contain no infrastructure dependencies

`backend/core/domain/` must not import:

- `backend.core.application`
- `backend.core.infrastructure`
- API or framework modules
- database libraries
- messaging libraries
- storage adapters

### Application Layer

`backend/core/application/` may import:

- `backend.core.domain`
- application-local modules
- contracts and ports
- approved shared modules

`backend/core/application/` must not import:

- `backend.core.infrastructure`
- concrete repositories
- concrete Unit of Work implementations
- SQLAlchemy
- FastAPI
- Redis clients
- MinIO clients

### Infrastructure Layer

`backend/core/infrastructure/` may import:

- `backend.core.domain`
- `backend.core.application`
- contracts and ports
- infrastructure libraries

Infrastructure is allowed to depend inward.

### Contracts

Contracts and ports must not depend on concrete infrastructure implementations.

## Implementation

Create architecture tests under:

`tests/architecture/`

Suggested files:

- `test_domain_dependencies.py`
- `test_application_dependencies.py`
- `test_contract_dependencies.py`

Use Python AST-based import inspection.

Do not introduce a large architecture framework unless it is clearly necessary.

Preferred approach:

1. Recursively scan Python files in the target layer.
2. Parse files with `ast`.
3. Extract `import` and `from ... import ...` statements.
4. Compare imports against forbidden module prefixes.
5. Produce a readable assertion message containing:
   - source file
   - forbidden import
   - violated rule

## Requirements

The architecture tests shall:

- work without importing the inspected modules;
- detect both `import x` and `from x import y`;
- scan nested packages;
- ignore virtual environments, cache directories and generated files;
- provide understandable failure messages;
- run as part of normal pytest execution.

Avoid fragile checks based only on plain text search.

## Import Validation

Keep the existing import validation working.

Architecture tests are additional protection and must not replace functional tests.

## Tests

Verify the architecture test helper itself with focused test cases where practical.

At minimum, confirm that it detects:

- Domain importing Infrastructure;
- Application importing Infrastructure;
- contracts importing concrete infrastructure.

Also confirm that valid inward dependencies pass.

## Documentation

Add a short architecture testing section to the relevant developer documentation.

Explain:

- which dependencies are allowed;
- which dependencies are forbidden;
- how to run the checks;
- how to interpret a failure.

Keep the documentation concise.

## Acceptance Criteria

- Domain-to-Infrastructure imports are automatically rejected.
- Domain-to-Application imports are automatically rejected.
- Application-to-Infrastructure imports are automatically rejected.
- Contracts cannot depend on concrete adapters.
- Valid inward dependencies remain allowed.
- Failure messages identify the file and forbidden import.
- Architecture tests run through `python3 -m pytest`.
- All existing tests pass.
- Ruff passes.
- Import validation passes.

## Non-Goals

- PostgreSQL
- SQLAlchemy
- FastAPI
- Event Bus
- Dependency injection container
- New business features
- Full static type checking migration
- Repository redesign

## Definition of Done

SafetyMAIN Core architectural boundaries are protected by executable automated tests.
