# TASK-P5-001

## Title

User Management API

## Status

Completed (2026-07-21)

## Summary

Introduced an administrative REST API for global user lifecycle management on top
of existing identity persistence and RBAC infrastructure.

## Endpoints

- `POST /api/v1/admin/users`
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/users/{user_id}`
- `PATCH /api/v1/admin/users/{user_id}`
- `POST /api/v1/admin/users/{user_id}/activate`
- `POST /api/v1/admin/users/{user_id}/deactivate`

## Permissions

- `user:read` — list/get
- `user:write` — create/update/activate/deactivate
- admin: read + write; auditor: read; member: none

## Validation Rules

- email format and uniqueness
- non-empty display name
- duplicate lifecycle transitions return `409`
- password hashes never exposed

## Tests Added

- `tests/core/test_user_administration_handlers.py`
- `tests/api/test_admin_users_api.py`
- Extended repository contract and OpenAPI tests

## Documentation

- [UserManagement.md](../docs/architecture/UserManagement.md)
- [AdminUserAPI.md](../docs/api/AdminUserAPI.md)
- Updated RoleBasedAuthorization.md, AuthenticationArchitecture.md, IdentityPersistence.md, docs/api/README.md

## Verification Results

- 459 passed, 68 skipped
- Ruff clean

## Follow-Up Work

- Password provisioning and reset flows
- Membership and organization administration APIs
