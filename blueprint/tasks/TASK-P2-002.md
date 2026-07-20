# TASK-P2-002

## Title

Implement Knowledge Object HTTP API

## Goal

Expose the existing Knowledge Object application use cases through versioned FastAPI endpoints.

## Acceptance Criteria

- Knowledge Object router is registered under `/api/v1/knowledge-objects`.
- Create, get, update, archive, restore, soft-delete, and history endpoints exist.
- Organization context is mandatory via `X-Organization-ID`.
- HTTP layer remains a thin inbound adapter over Application handlers.
- API tests run without PostgreSQL.
