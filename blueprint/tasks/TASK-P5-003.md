# TASK-P5-003

## Title

Membership Management API

## Status

Completed (2026-07-21)

## Endpoints

- `POST /api/v1/admin/memberships`
- `GET /api/v1/admin/memberships`
- `GET /api/v1/admin/memberships/{membership_id}`
- `PATCH /api/v1/admin/memberships/{membership_id}/role`
- `POST /api/v1/admin/memberships/{membership_id}/activate`
- `POST /api/v1/admin/memberships/{membership_id}/deactivate`

## Permissions

- `membership:read`, `membership:write`
- admin: read + write; auditor: read; member: none

## Safety Rules

- Self deactivation of authorization membership
- Self admin role downgrade
- Last active administrator protection (target organization)

Implemented in Application layer: `membership_administration.py`.

## Repository Changes

- `list_memberships(MembershipListCriteria)`
- `MembershipByIdNotFound` for get-by-id

## Tests Added

- `tests/core/test_membership_administration_handlers.py`
- `tests/api/test_admin_memberships_api.py`
- Extended membership repository contract tests

## Documentation

- [MembershipManagement.md](../docs/architecture/MembershipManagement.md)
- [AdminMembershipAPI.md](../docs/api/AdminMembershipAPI.md)

## Verification Results

- 493 passed, 72 skipped
- Ruff clean

## Follow-Up Work

- Invitation workflows
- Membership audit logging
