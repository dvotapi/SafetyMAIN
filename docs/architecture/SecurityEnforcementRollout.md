# Security Enforcement Rollout

Status: Active  
Date: 2026-07-21  
Task: TASK-P4-002

Related documents:

- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)
- [AuthorizationFoundation.md](AuthorizationFoundation.md)
- [TenantContextMigration.md](TenantContextMigration.md)
- [SecurityArchitectureReview.md](SecurityArchitectureReview.md)

---

## 1. Enforcement Objective

Phase P4-002 applies the Phase P3 authentication, tenant membership, and RBAC
infrastructure to all Knowledge Object and Relation business endpoints.

When `AUTH_ENFORCEMENT=true`, every business operation requires:

1. a valid Bearer access token;
2. resolvable organization context;
3. active organization membership;
4. a role permission matching the operation category.

When `AUTH_ENFORCEMENT=false`, the documented compatibility mode remains
available: header-only tenant context and permission dependencies behave as
no-ops.

No new roles, permissions, or authorization mechanisms were introduced.

---

## 2. Permission Matrix

Policy constants live in
`backend/core/application/authorization/policies/resource_permissions.py`.
Domain permissions remain defined in
`backend/core/domain/value_objects/permission.py`.

| HTTP | Route | Operation | Required policy | Domain permission | admin | member | auditor |
|------|-------|-----------|-----------------|-------------------|-------|--------|---------|
| POST | `/api/v1/knowledge-objects` | Create | `KNOWLEDGE_OBJECT_WRITE` | `knowledge_object:write` | allow | allow | deny |
| GET | `/api/v1/knowledge-objects` | Search | `KNOWLEDGE_OBJECT_READ` | `knowledge_object:read` | allow | allow | allow |
| GET | `/api/v1/knowledge-objects/{id}` | Get | `KNOWLEDGE_OBJECT_READ` | `knowledge_object:read` | allow | allow | allow |
| PUT | `/api/v1/knowledge-objects/{id}` | Update | `KNOWLEDGE_OBJECT_WRITE` | `knowledge_object:write` | allow | allow | deny |
| POST | `/api/v1/knowledge-objects/{id}/archive` | Archive | `KNOWLEDGE_OBJECT_WRITE` | `knowledge_object:write` | allow | allow | deny |
| POST | `/api/v1/knowledge-objects/{id}/restore` | Restore | `KNOWLEDGE_OBJECT_WRITE` | `knowledge_object:write` | allow | allow | deny |
| DELETE | `/api/v1/knowledge-objects/{id}` | Soft-delete | `KNOWLEDGE_OBJECT_DELETE` | `knowledge_object:write` | allow | allow | deny |
| GET | `/api/v1/knowledge-objects/{id}/history` | Version history | `KNOWLEDGE_OBJECT_READ` | `knowledge_object:read` | allow | allow | allow |
| GET | `/api/v1/knowledge-objects/{id}/relations/outgoing` | Outgoing traversal | `RELATION_READ` | `relation:manage` | allow | allow | deny |
| GET | `/api/v1/knowledge-objects/{id}/relations/incoming` | Incoming traversal | `RELATION_READ` | `relation:manage` | allow | allow | deny |
| GET | `/api/v1/knowledge-objects/{id}/connected` | Connected objects | `RELATION_READ` | `relation:manage` | allow | allow | deny |
| POST | `/api/v1/relations` | Create relation | `RELATION_WRITE` | `relation:manage` | allow | allow | deny |
| GET | `/api/v1/relations/{id}` | Get relation | `RELATION_READ` | `relation:manage` | allow | allow | deny |
| DELETE | `/api/v1/relations/{id}` | Delete relation | `RELATION_DELETE` | `relation:manage` | allow | allow | deny |

**Classification notes**

- Soft-delete uses `KNOWLEDGE_OBJECT_DELETE`, which maps to `knowledge_object:write`
  because the domain model does not define a separate delete permission.
- Relation read/write/delete policies all map to `relation:manage` because P3-002
  defines a single relation capability.
- Traversal and graph queries require `RELATION_READ` (`relation:manage`), not
  `KNOWLEDGE_OBJECT_READ`.

---

## 3. Route Classification

| Category | Endpoints | Policy |
|----------|-----------|--------|
| Knowledge Object read | get, search, history | `KNOWLEDGE_OBJECT_READ` |
| Knowledge Object write | create, update, archive, restore | `KNOWLEDGE_OBJECT_WRITE` |
| Knowledge Object delete | soft-delete | `KNOWLEDGE_OBJECT_DELETE` |
| Relation read | get relation, traversal endpoints | `RELATION_READ` |
| Relation write | create relation | `RELATION_WRITE` |
| Relation delete | delete relation | `RELATION_DELETE` |

---

## 4. Authorization Sequence

```text
1. Authenticate caller (when AUTH_ENFORCEMENT=true)
2. Resolve tenant context (token org → header → default → sole membership)
3. Reject conflicting organization contexts (422)
4. Verify active organization membership (403 organization_access_denied)
5. Resolve membership role
6. Evaluate required permission (403 permission_denied)
7. Execute business handler
8. Preserve repository/Application tenant filtering
```

Permission evaluation never runs before membership verification. Business resource
lookup is not used as a substitute for membership authorization.

---

## 5. Compatibility Mode

`AUTH_ENFORCEMENT=false` (default):

- `X-Organization-ID` remains the tenant selector;
- anonymous business requests continue to work;
- `require_permission()` is a no-op;
- JWT authentication endpoints remain available;
- legacy success responses are unchanged.

---

## 6. Enforced Mode

`AUTH_ENFORCEMENT=true`:

- protected business routes require a valid Bearer access token;
- refresh tokens cannot authorize business requests;
- the user must have active membership in the selected organization;
- the membership role must include the endpoint permission;
- missing permission returns `403 permission_denied`;
- handlers are not executed after authorization failure.

---

## 7. Role Behavior

Role-to-permission mapping is unchanged and validated via existing domain policy:

| Role | Effective permissions |
|------|----------------------|
| `admin` | All `SystemPermission` values |
| `member` | `knowledge_object:read`, `knowledge_object:write`, `relation:manage` |
| `auditor` | `knowledge_object:read` only |
| unknown | empty set (fail closed) |

---

## 8. OpenAPI Behavior

OpenAPI describes the **enforced-mode contract** statically:

- all Knowledge Object and Relation operations declare `security: [BearerAuth]`;
- authentication and system routes remain public;
- protected operations document `401` and `403` responses using the common error envelope;
- operation IDs remain stable.

Compatibility mode behavior is not reflected in OpenAPI because generation is
not environment-aware. Clients migrating from header-only access should consult
this document and [TenantContextMigration.md](TenantContextMigration.md).

---

## 9. Error Semantics

| Situation | HTTP | Public code |
|-----------|------|-------------|
| Missing Bearer token (enforced mode) | 401 | `unauthenticated` |
| Invalid or expired access token | 401 | `unauthenticated` |
| Refresh token used as access token | 401 | `unauthenticated` |
| Missing active membership | 403 | `organization_access_denied` |
| Insufficient role permission | 403 | `permission_denied` |
| Conflicting token/header organization | 422 | `organization_context_required` |
| Missing resolvable organization context | 422 | `organization_context_required` |
| Cross-organization resource lookup after valid authorization | 404 | domain codes |

Authorization failures use the common API error envelope and do not leak token
payloads, passwords, membership internals, role mappings, or cross-organization
resource existence.

---

## 10. Rollout Guidance

1. Deploy with `AUTH_ENFORCEMENT=false` while clients adopt Bearer tokens.
2. Seed identity and membership data (see [IdentityPersistence.md](IdentityPersistence.md)).
3. Validate clients against enforced mode in staging (`AUTH_ENFORCEMENT=true`).
4. Enable enforced mode in production after client migration.
5. Retire compatibility mode only after all consumers send Bearer access tokens.

---

## 11. Known Limitations

1. OpenAPI always documents Bearer requirements even when compatibility mode is active.
2. Relation traversal requires `relation:manage`; auditors cannot traverse relations.
3. Compatibility mode remains available until explicitly retired in a future phase.
4. No audit logging of authorization decisions (out of scope).

---

## 12. Implementation Status

| Area | Status |
|------|--------|
| Knowledge Object route enforcement | Implemented |
| Relation route enforcement | Implemented |
| Traversal/search classification | Implemented |
| Compatibility mode | Preserved |
| OpenAPI enforced contract | Implemented |
| Route-level test matrix | `tests/api/test_business_route_enforcement.py` |
| Architecture guardrails | Extended |

Remaining production deployment actions: enable `AUTH_ENFORCEMENT=true`, configure
production JWT secrets, and run identity seed/migration in target environments.
