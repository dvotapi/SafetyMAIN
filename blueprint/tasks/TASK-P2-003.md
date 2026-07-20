# TASK-P2-003

## Title

Implement Knowledge Object Relation HTTP API

## Goal

Expose relation create/get/delete and one-hop traversal endpoints through versioned FastAPI routes.

## Acceptance Criteria

- Relation router registered under `/api/v1/relations`.
- Traversal endpoints exposed on Knowledge Object paths.
- Organization context enforced in Application via `X-Organization-ID`.
- API tests run without PostgreSQL.
