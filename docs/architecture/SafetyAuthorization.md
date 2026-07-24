# Safety Authorization

Status: Implemented (TASK-P8-002)

Hazard permissions extend the existing RBAC model (`SystemPermission` + role map).

## Permissions

- `hazard:read`
- `hazard:create`
- `hazard:update`
- `hazard:activate`
- `hazard:archive`
- `hazard:restore`

## Role mapping

- Admin: all hazard permissions (inherits all system permissions)
- Member: read, create, update
- Auditor: read only

Route handlers use `require_permission(...)` and do not embed authorization logic.

## Risk assessment permissions (TASK-P8-003)

- `risk:read`, `risk:create`, `risk:update`, `risk:review`, `risk:approve`, `risk:archive`
- Admin: all; Member: read/create/update; Auditor: read

Permission denials for hazard permissions are audited through the existing
administrative denial path with resource type `HAZARD`.
