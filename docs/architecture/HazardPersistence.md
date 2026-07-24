# Hazard Persistence

Status: Implemented (TASK-P8-002)

## Table

`safety_hazards` (Alembic revision `0010_safety_hazards`).

## Multi-value classifications

`safety_directions` and `affected_subjects` are stored as PostgreSQL `text[]`
columns with GIN indexes.

Trade-off:

- Arrays keep the row model simple and support indexed containment queries.
- Normalized child tables would be better for heavy analytics joins later.
- Opaque JSONB blobs were rejected for these searchable classifications.

`extension_references` uses JSONB for optional Russian-practice pointers that are
not primary list filters in this task.

## Constraints and indexes

- PK on `id`
- FK to `organizations.id`
- Unique `(organization_id, code)`
- Non-empty title check
- Status/category check constraints
- Positive `version`
- Indexes on organization-scoped status/category/created_at/identified_at

## Optimistic concurrency

`save(..., expected_version=...)` updates with `WHERE version = expected_version`.
Zero rows mapped to `HazardVersionConflict` (or `HazardNotFound`).

## Repository implementations

- `InMemoryHazardRepository` — contract parity for non-DB tests
- `SQLAlchemyHazardRepository` — production path when `DATABASE_URL` is configured

Repositories never commit; Unit of Work owns transactions.
