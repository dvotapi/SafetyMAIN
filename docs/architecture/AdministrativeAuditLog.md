# Administrative Audit Log

Status: Active  
Date: 2026-07-24  
Task: TASK-P5-005, TASK-P6-001, TASK-P6-002

Related documents:

- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)
- [UserManagement.md](UserManagement.md)
- [OrganizationManagement.md](OrganizationManagement.md)
- [MembershipManagement.md](MembershipManagement.md)
- [InvitationWorkflow.md](InvitationWorkflow.md)
- [AdminAuditAPI.md](../api/AdminAuditAPI.md)
- [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md)

---

## 1. Purpose and Threat Model

SafetyMAIN records security-relevant administrative actions performed through identity,
organization, membership, and invitation workflows.

The audit log supports:

- accountability for privileged changes;
- investigation of rejected administrative attempts with stable failure codes;
- scoped read access for organization administrators and auditors.

Audit events are not a SIEM, legal-hold system, or cryptographic tamper-evidence chain.
They are append-only application records stored in the primary database.

---

## 2. Audit Event Model

`AuditEvent` is an immutable domain entity with:

| Field | Description |
|-------|-------------|
| `id` | Public UUID |
| `actor_user_id` | Authenticated actor from `SecurityContext`, when available |
| `authorization_organization_id` | Organization whose membership authorized the action |
| `target_organization_id` | Organization affected by the operation, when applicable |
| `action` | Stable action identifier (`<resource>.<operation>`) |
| `resource_type` | Stable resource type (`USER`, `ORGANIZATION`, `MEMBERSHIP`, `INVITATION`, `AUDIT_EVENT`) |
| `resource_id` | Affected resource identifier, when available |
| `outcome` | `SUCCESS` or `FAILURE` |
| `failure_code` | Stable application code for expected failures |
| `metadata` | Allowlisted JSON-compatible fields |
| `occurred_at` | UTC timestamp |

Audit events have no update, delete, activate, or deactivate lifecycle.

---

## 3. Action Taxonomy

Actions are centralized in `AuditAction`:

- User: `user.create`, `user.update`, `user.activate`, `user.deactivate`
- Organization: `organization.create`, `organization.update`, `organization.activate`, `organization.deactivate`
- Membership: `membership.create`, `membership.role_change`, `membership.activate`, `membership.deactivate`
- Invitation: `invitation.create`, `invitation.revoke`, `invitation.reissue`, `invitation.accept`
- Authorization: `authorization.permission_denied`

Handlers and centralized authorization dependencies must not use arbitrary free-form action strings.

All published administrative audit action identifiers are registered in the immutable
Security Event Taxonomy Registry. See [SecurityEventTaxonomy.md](SecurityEventTaxonomy.md).

---

## 4. Actor Context

Actor identity comes from trusted application context:

- `SecurityContext.user_id` for administrative mutations;
- `TenantContext.organization_id` for authorization organization;
- invitation acceptance uses the authenticated accepting user and may omit authorization organization.

API clients cannot supply actor, authorization organization, outcome, or timestamp.

---

## 5. Authorization Organization vs Target Organization

These values are stored separately:

- **Authorization organization** — membership context that granted permission (`TenantContext.organization_id`).
- **Target organization** — organization affected by the operation (for example invitation target org or membership org).

They may match, but must not be inferred from each other.

---

## 6. Success Transaction Behavior

Successful administrative mutations and their audit events commit in the same Unit of
Work transaction through `AdministrativeAuditRecorder.record_success()` followed by
`unit_of_work.commit()`.

`run_audited_admin_operation()` opens a transaction boundary (`begin()` / context
manager), records the success audit event into the same Unit of Work, and commits
once. If commit fails, the Unit of Work rolls back both the business mutation and the
success audit event.

SQLAlchemy uses one database session/transaction for all repositories, including
`audit_events`. In-memory Unit of Work snapshots identity and audit repositories so
test and non-SQL paths preserve the same all-or-nothing semantics.

---

## 7. Failure Recording Behavior

Expected business failures use a separate audit transaction through `record_failure()` /
`record_known_failure()` **after** the business Unit of Work rolls back. A rolled-back
business transaction cannot persist the failure audit event itself.

If failure-audit persistence also fails:

- the original API/business error is preserved;
- a safe application log entry is emitted;
- audit infrastructure details are not exposed to clients.

---

## 8. Permission-Denial Auditing (TASK-P6-001)

Authenticated administrative permission denials are recorded when all of the following
are true before the protected handler executes:

- Bearer authentication succeeded and JWT validation completed;
- a trusted `SecurityContext` exists with an active actor user;
- `TenantContext` resolved an authorization organization;
- active membership was verified through existing organization-access rules;
- permission evaluation denied the required administrative permission.

Integration point: centralized `require_permission()` in the API layer. The dependency
calls `AdministrativeAuditRecorder.record_permission_denial()` with a
`PermissionDenialAuditSpec` built from trusted security context and sanitized route
metadata. Business endpoint denials (`knowledge_object:*`, `relation:*`) are not
written to the administrative audit log in this task.

### Eligibility exclusions

Do **not** create permission-denial audit events for:

- missing, malformed, expired, or invalid JWT authentication (`401`);
- unresolved or conflicting organization context (`422`);
- missing or inactive membership rejected before permission evaluation;
- anonymous compatibility-mode requests when `AUTH_ENFORCEMENT=false`.

### Event shape

| Field | Value |
|-------|-------|
| `action` | `authorization.permission_denied` |
| `outcome` | `FAILURE` |
| `failure_code` | `permission_denied` |
| `actor_user_id` | `SecurityContext.user_id` |
| `authorization_organization_id` | `TenantContext.organization_id` |
| `resource_type` | Mapped from required permission (`user:read` → `USER`, `audit:read` → `AUDIT_EVENT`, …) |
| `resource_id` | Path UUID when safely available before handler execution; otherwise absent |
| `target_organization_id` | Validated path/DTO organization when safely available; otherwise absent |

Metadata allowlist for permission denial:

- `required_permission`
- `http_method`
- `route_template` (normalized API prefix, not raw sensitive URLs)
- `operation_id` (optional)
- `target_identifier_present`
- `permission_category`

### Transaction model

Permission denial occurs before any business mutation. The audit event is persisted in
a dedicated failure Unit of Work through `record_permission_denial()` and committed
independently. If audit persistence fails, the original `403 permission_denied` response
is preserved and a safe operational log is emitted.

Exactly one permission-denial audit attempt is made per denied request. The global HTTP
exception mapper does not duplicate this work.

Each API route handler must declare at most one `require_permission()` dependency.
Multiple guards on the same handler would run separate permission checks and could emit
duplicate permission-denial audit events.

---

## 9. Immutable Persistence

Repository ports support `add`, `get`, and `list_events` only.

Table: `audit_events` (Alembic revision `0005_audit_events`).

There is no public audit-write permission or HTTP mutation endpoint.

---

## 10. Query Scoping

Read queries are scoped from trusted tenant context:

- include events where `authorization_organization_id` equals the current organization;
- also include events where `target_organization_id` equals the current organization;
- out-of-scope event IDs return `404`.

---

## 11. Metadata Allowlisting

Allowed metadata keys:

- `changed_fields`
- `previous_role`, `new_role`
- `previous_status`, `new_status`
- `expiration_refreshed`
- `membership_id`
- `required_permission`, `http_method`, `route_template`
- `operation_id`, `target_identifier_present`, `permission_category`

Metadata must not contain entity snapshots, request bodies, secrets, tokens, or raw exception text.

---

## 12. Sensitive-Data Exclusions

Audit records must never contain:

- passwords or password hashes;
- JWTs or authorization headers;
- invitation plaintext tokens or token hashes;
- database credentials;
- raw request bodies;
- stack traces or arbitrary exception messages.

---

## 13. Supported Administrative Events

All P5 administrative write handlers record success events. Representative expected failures are mapped to stable codes in `AUDITABLE_ADMIN_FAILURES`.

Permission-denial events (`authorization.permission_denied`) are recorded for authenticated administrative RBAC denials when trusted actor and tenant context exist.

Invitation acceptance records `invitation.accept` with optional `membership_id` metadata and never stores token material.

---

## 14. Known Limitations

- Business endpoint permission denials are not recorded in the administrative audit log.
- Authentication failures (`401`) and pre-permission tenant/membership failures are not administrative audit events.
- No platform-wide cross-organization audit view for ordinary org admins.
- No retention, export, signing, or external streaming integration.

---

## 15. Future Considerations

Follow-up work may include business security-event auditing, retention policies, export formats, and platform administrator roles.
