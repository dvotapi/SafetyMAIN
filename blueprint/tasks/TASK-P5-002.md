# TASK-P5-002

## Title

Organization Management API

## Status

Completed (2026-07-21)

## Summary

Introduced an administrative REST API for global organization lifecycle management on
top of existing identity persistence, UnitOfWork, and RBAC infrastructure.

## Domain Changes

- `Organization.status`, `Organization.updated_at`
- `OrganizationListCriteria` / `OrganizationListResult`
- Exceptions for duplicate names, lifecycle conflicts, and self-deactivation

## Permission Changes

- `organization:read`, `organization:write`
- admin: read + write; auditor: read; member: none

## Endpoints

- `POST /api/v1/admin/organizations`
- `GET /api/v1/admin/organizations`
- `GET /api/v1/admin/organizations/{organization_id}`
- `PATCH /api/v1/admin/organizations/{organization_id}`
- `POST /api/v1/admin/organizations/{organization_id}/activate`
- `POST /api/v1/admin/organizations/{organization_id}/deactivate`

## Name Uniqueness Policy

Trim whitespace, reject empty names, max length 255, case-insensitive duplicate
detection via normalized name key, unique DB index on `lower(name)`.

## Lifecycle Decisions

- Reversible active/deactivated states
- Repeated lifecycle operations return `409`
- No deletion endpoint
- Memberships unchanged by lifecycle operations

## Self-Deactivation Rule

Deactivating the current authorization organization returns
`409 current_organization_deactivation`.

## Repository Changes

- `get_by_normalized_name`
- `list_organizations`

## Migrations

- `0003_organization_active_state` — `organizations.is_active`, unique normalized name index

## Tests Added

- `tests/core/test_organization_administration_handlers.py`
- `tests/api/test_admin_organizations_api.py`
- `OrganizationRepositoryContractSuite` (in-memory and SQLAlchemy)

## Documentation

- [OrganizationManagement.md](../docs/architecture/OrganizationManagement.md)
- [AdminOrganizationAPI.md](../docs/api/AdminOrganizationAPI.md)
- Updated RoleBasedAuthorization.md, IdentityPersistence.md, UserManagement.md, docs/api/README.md

## Verification Results

- 480 passed, 71 skipped
- Ruff clean

## Follow-Up Work

- Membership administration API
- Organization settings and ownership models
