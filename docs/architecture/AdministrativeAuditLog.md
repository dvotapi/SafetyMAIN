# Administrative Audit Log

Status: Active  
Date: 2026-07-21  
Task: TASK-P5-005

Related documents:

- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)
- [UserManagement.md](UserManagement.md)
- [OrganizationManagement.md](OrganizationManagement.md)
- [MembershipManagement.md](MembershipManagement.md)
- [InvitationWorkflow.md](InvitationWorkflow.md)
- [AdminAuditAPI.md](../api/AdminAuditAPI.md)

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
| `resource_type` | Stable resource type (`USER`, `ORGANIZATION`, `MEMBERSHIP`, `INVITATION`) |
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

Handlers must not use arbitrary free-form action strings.

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

Permission denials before trusted actor context exists are not recorded in the audit table.

---

## 8. Immutable Persistence

Repository ports support `add`, `get`, and `list_events` only.

Table: `audit_events` (Alembic revision `0005_audit_events`).

There is no public audit-write permission or HTTP mutation endpoint.

---

## 9. Query Scoping

Read queries are scoped from trusted tenant context:

- include events where `authorization_organization_id` equals the current organization;
- also include events where `target_organization_id` equals the current organization;
- out-of-scope event IDs return `404`.

---

## 10. Metadata Allowlisting

Allowed metadata keys:

- `changed_fields`
- `previous_role`, `new_role`
- `previous_status`, `new_status`
- `expiration_refreshed`
- `membership_id`

Metadata must not contain entity snapshots, request bodies, secrets, tokens, or raw exception text.

---

## 11. Sensitive-Data Exclusions

Audit records must never contain:

- passwords or password hashes;
- JWTs or authorization headers;
- invitation plaintext tokens or token hashes;
- database credentials;
- raw request bodies;
- stack traces or arbitrary exception messages.

---

## 12. Supported Administrative Events

All P5 administrative write handlers record success events. Representative expected failures are mapped to stable codes in `AUDITABLE_ADMIN_FAILURES`.

Invitation acceptance records `invitation.accept` with optional `membership_id` metadata and never stores token material.

---

## 13. Known Limitations

- Permission-denied auditing inside `require_permission()` is deferred.
- No platform-wide cross-organization audit view for ordinary org admins.
- No retention, export, signing, or external streaming integration.

---

## 14. Future Considerations

Follow-up work may include retention policies, export formats, platform administrator roles, and optional permission-denial auditing once authorization integration can remain narrow.
