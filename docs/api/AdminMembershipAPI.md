# Admin Membership API

Status: Active  
Date: 2026-07-21  
Task: TASK-P5-003

Related documents:

- [MembershipManagement.md](../architecture/MembershipManagement.md)
- [AdminOrganizationAPI.md](AdminOrganizationAPI.md)
- [AdminUserAPI.md](AdminUserAPI.md)

---

## Endpoints

| Method | Path | Operation ID | Permission |
|--------|------|--------------|------------|
| POST | `/api/v1/admin/memberships` | `create_membership` | `membership:write` |
| GET | `/api/v1/admin/memberships` | `list_memberships` | `membership:read` |
| GET | `/api/v1/admin/memberships/{membership_id}` | `get_membership` | `membership:read` |
| PATCH | `/api/v1/admin/memberships/{membership_id}/role` | `update_membership_role` | `membership:write` |
| POST | `/api/v1/admin/memberships/{membership_id}/activate` | `activate_membership` | `membership:write` |
| POST | `/api/v1/admin/memberships/{membership_id}/deactivate` | `deactivate_membership` | `membership:write` |

---

## Membership Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "11111111-1111-1111-1111-111111111111",
  "user_id": "22222222-2222-2222-2222-222222222222",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-07-21T10:00:00Z",
  "updated_at": "2026-07-21T10:00:00Z"
}
```

---

## Create Membership

```json
{
  "user_id": "22222222-2222-2222-2222-222222222222",
  "organization_id": "11111111-1111-1111-1111-111111111111",
  "role": "member",
  "is_active": true
}
```

---

## List Memberships

Required query parameter: `organization_id`.

Optional filters: `user_id`, `role`, `is_active`, `offset`, `limit`, `sort_asc`.

---

## Lifecycle Conflicts

| Operation | Conflict code |
|-----------|---------------|
| Activate active membership | `membership_already_active` |
| Deactivate inactive membership | `membership_already_inactive` |
| Deactivate authorization membership | `self_membership_deactivation` |
| Downgrade authorization admin role | `self_membership_role_downgrade` |
| Remove last administrator | `last_organization_administrator` |

---

## Authorization Matrix

| Role | List/Get | Create/Update/Lifecycle |
|------|----------|-------------------------|
| admin | allowed | allowed |
| auditor | allowed | denied (`403`) |
| member | denied (`403`) | denied (`403`) |

Unknown roles fail closed.
