# TASK-P4-002

## Title

Security Enforcement Rollout

## Status

Completed (2026-07-21)

## Summary

Applied existing authentication, tenant membership, and RBAC enforcement to all
Knowledge Object and Relation business API routes via `require_permission()`,
while preserving compatibility mode through `AUTH_ENFORCEMENT=false`.

## Permission Matrix

Documented in [SecurityEnforcementRollout.md](../docs/architecture/SecurityEnforcementRollout.md).

14 business endpoints classified across read/write/delete policies for Knowledge
Objects and Relations, including traversal and search operations.

## Routes Updated

- `backend/api/routers/knowledge_objects.py` — 11 endpoints
- `backend/api/routers/relations.py` — 3 endpoints

## Tests Added

- `tests/api/test_business_route_enforcement.py` — route-level enforcement matrix
- Extended `tests/api/contracts/test_openapi.py` — BearerAuth on business routes
- Extended `tests/architecture/test_security_boundaries.py` — enforcement guardrails
- Extended `tests/architecture/architecture_imports.py` — assignment guard helper
- Extended helper headers support in knowledge object/relation test helpers

## OpenAPI Changes

- `backend/api/openapi.py` — `PROTECTED_BUSINESS_ERROR_RESPONSES`
- `backend/api/app.py` — post-process business routes with `BearerAuth` security
- Business routes document `401`/`403` error responses

## Compatibility Decisions

- `AUTH_ENFORCEMENT=false` keeps header-only anonymous access; permission deps are no-ops
- OpenAPI describes enforced-mode contract statically (documented limitation retained)

## Validation Results

- Full pytest suite
- Ruff clean
- Architecture tests pass
- PostgreSQL integration tests available with `SAFETYMAIN_RUN_DB_TESTS=1`

## Discovered Limitations

- Auditors cannot access relation or traversal endpoints (by design — no `relation:manage`)
- OpenAPI cannot vary by runtime enforcement mode

## Follow-Up Work

- Enable `AUTH_ENFORCEMENT=true` in production after client migration
- Retire compatibility mode in a future phase when all clients use Bearer tokens
