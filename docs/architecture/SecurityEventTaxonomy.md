# Security Event Taxonomy

Status: Active  
Date: 2026-07-24  
Task: TASK-P6-002

Related documents:

- [AdministrativeAuditLog.md](AdministrativeAuditLog.md)
- [AuthorizationFoundation.md](AuthorizationFoundation.md)
- [RoleBasedAuthorization.md](RoleBasedAuthorization.md)
- [AuthenticationArchitecture.md](AuthenticationArchitecture.md)
- [SecurityArchitectureReview.md](SecurityArchitectureReview.md)

---

## 1. Auditable Security Event

An **Auditable Security Event** is an immutable persisted record of a security-relevant
fact produced by an authoritative application or security boundary.

This taxonomy governs persisted audit records in the `audit_events` store.

Out of scope for this taxonomy:

- transient metrics;
- unstructured log messages;
- derived detections, alerts, or notifications;
- SIEM correlation rules;
- non-persisted operational telemetry.

---

## 2. Event Instance Identity vs Event Type Identity

**Event instance identity** is the unique ID of one persisted `AuditEvent` record.
The taxonomy registry does not replace instance IDs.

**Event type identity** is the stable published identifier describing the semantic type
of an event, for example:

```text
authorization.permission_denied
```

Event type identifiers are:

- stable;
- lowercase;
- dot-separated;
- defined centrally in `AuditAction` and the Security Event Registry;
- independent from Python class names, module paths, and HTTP route names.

Producers must not dynamically assemble event type identifiers at runtime.

---

## 3. Security Decision Occurrence

A **Security Decision Occurrence** is one completed security decision for one logical
subject or resource within one execution context.

Examples:

- one permission evaluation for one protected HTTP request;
- one administrative mutation attempt;
- one expected business failure mapped to a stable audit failure code.

A decision occurrence is not equivalent to a route path, endpoint definition, client
session, correlation ID, or event instance ID.

---

## 4. Duplicate Production Semantics

For one authoritative decision occurrence, the authoritative producer emits at most one
event of the same event type.

Existing Authorization invariant:

> One denied HTTP request guarded by `require_permission()` persists exactly one
> `authorization.permission_denied` event.

Multiple events of the same type within one request may be valid when the request
intentionally processes multiple logical resources. Duplicate prevention is scoped to
the authoritative decision occurrence, not to the entire HTTP request globally.

---

## 5. Primary Event Categories

Primary category describes the security nature of the event.

| Category | Purpose |
|----------|---------|
| `ADMINISTRATIVE` | Privileged identity and organization administration |
| `AUTHENTICATION` | Credential and identity verification (future) |
| `AUTHORIZATION` | Permission and access-control decisions |
| `SECURITY_INFRASTRUCTURE` | Audit or security platform degradation (future) |

Primary category is orthogonal to subject domain.

---

## 6. Subject Domains

Subject domain describes the resource or subsystem affected by the event.

Supported values include:

```text
USER
IDENTITY
ORGANIZATION
MEMBERSHIP
INVITATION
SESSION
CREDENTIAL
API_KEY
AUDIT_EVENT
SECURITY_SYSTEM
```

`resource_type` on persisted `AuditEvent` records remains unchanged. Subject domain is
a normalized taxonomy classification and does not replace persisted resource types.

---

## 7. Producer Ownership

Producer ownership identifies the architectural capability responsible for deciding
that an event occurred.

| Producer owner | Role |
|----------------|------|
| `ADMINISTRATIVE_AUDIT` | Centralized administrative operation audit boundary |
| `AUTHORIZATION` | Centralized permission authorization boundary |
| `AUTHENTICATION` | Future authentication application services |
| `SECURITY_INFRASTRUCTURE` | Future security infrastructure degradation handling |

Producer ownership refers to an architectural role, not a concrete Python class,
function, module, or repository.

---

## 8. Trigger Owner, Builder, Recorder, Repository

| Role | Responsibility |
|------|----------------|
| Trigger owner | Authoritative boundary that knows the security fact occurred |
| Builder / spec factory | Constructs a validated event specification from trusted context |
| Recorder | Validates, normalizes, and persists through the transaction boundary |
| Repository | Appends an already validated event record |

Current mappings:

| Event family | Trigger owner | Recorder |
|--------------|---------------|----------|
| Administrative Audit | `run_audited_admin_operation()` / handler boundary | `AdministrativeAuditRecorder` |
| Authorization Permission Denial | `require_permission()` | `AdministrativeAuditRecorder.record_permission_denial()` |

The recorder does not redefine event type identity or producer ownership.

---

## 9. Outcome Compatibility

The taxonomy reuses the existing audit outcome model:

```text
SUCCESS
FAILURE
```

No additional outcome values are introduced by P6-002.

Authorization Permission Denial continues to persist `FAILURE` only.

---

## 10. Optional Security Significance

Registry descriptors may include optional static `default_security_significance`:

```text
INFORMATIONAL
LOW
MEDIUM
HIGH
CRITICAL
```

Significance is registry metadata only. It is not persisted in `AuditEvent`, not exposed
through the Audit API, and not used for alerting in this task.

---

## 11. Current Published Event Inventory

All identifiers below are registered in `SECURITY_EVENT_REGISTRY` and published through
`AuditAction`.

### Administrative Audit (`ADMINISTRATIVE` / `ADMINISTRATIVE_AUDIT`)

| Event type | Subject domain | Outcomes |
|------------|----------------|----------|
| `user.create` | `USER` | SUCCESS, FAILURE |
| `user.update` | `USER` | SUCCESS, FAILURE |
| `user.activate` | `USER` | SUCCESS, FAILURE |
| `user.deactivate` | `USER` | SUCCESS, FAILURE |
| `organization.create` | `ORGANIZATION` | SUCCESS, FAILURE |
| `organization.update` | `ORGANIZATION` | SUCCESS, FAILURE |
| `organization.activate` | `ORGANIZATION` | SUCCESS, FAILURE |
| `organization.deactivate` | `ORGANIZATION` | SUCCESS, FAILURE |
| `membership.create` | `MEMBERSHIP` | SUCCESS, FAILURE |
| `membership.role_change` | `MEMBERSHIP` | SUCCESS, FAILURE |
| `membership.activate` | `MEMBERSHIP` | SUCCESS, FAILURE |
| `membership.deactivate` | `MEMBERSHIP` | SUCCESS, FAILURE |
| `invitation.create` | `INVITATION` | SUCCESS, FAILURE |
| `invitation.revoke` | `INVITATION` | SUCCESS, FAILURE |
| `invitation.reissue` | `INVITATION` | SUCCESS, FAILURE |
| `invitation.accept` | `INVITATION` | SUCCESS, FAILURE |

### Authorization Permission Denial (`AUTHORIZATION` / `AUTHORIZATION`)

| Event type | Subject domain | Outcomes | Significance |
|------------|----------------|----------|--------------|
| `authorization.permission_denied` | `SECURITY_SYSTEM` | FAILURE | MEDIUM |

All current identifiers are registered as legacy-compatible because they predate the
preferred `<category>.<subject>.<action>` naming convention.

---

## 12. Registry Architecture

Implementation location:

```text
backend/core/domain/security_events/
```

Key modules:

- `descriptor.py` — immutable `SecurityEventDescriptor`
- `families/administrative.py` — administrative descriptors
- `families/authorization.py` — authorization descriptors
- `registry.py` — centralized immutable `SECURITY_EVENT_REGISTRY`
- `validation.py` — registry validation
- `naming.py` — preferred naming convention rules

The registry is initialized deterministically from source-controlled definitions.
Runtime dynamic registration is not supported.

---

## 13. Future Event Naming Rules

Future event identifiers should follow:

```text
<category>.<subject>.<action>
```

Examples:

```text
authentication.credential.rejected
authentication.session.created
administrative.invitation.revoked
security.audit.persistence_failed
```

Future identifiers must:

- use lowercase ASCII;
- use dot separators;
- describe completed facts;
- remain stable after publication.

Existing identifiers must not be renamed to force compliance.

---

## 14. Organization Context Semantics

Persisted audit records preserve the distinction between:

- `authorization_organization_id` — organization whose membership authorized the actor;
- `target_organization_id` — organization owning or affected by the target resource.

These values may match but must not be inferred from each other. The registry is static
metadata and does not perform tenant resolution.

---

## 15. Compatibility Mode

When `AUTH_ENFORCEMENT=false`:

- the registry does not activate authentication enforcement;
- the registry does not create authorization events where none existed;
- anonymous compatibility behavior remains unchanged.

Future event families must document compatibility-mode behavior explicitly.

---

## 16. Authentication Extension Compatibility

Future Authentication Events may occur without actor user ID, organization ID,
`SecurityContext`, or `TenantContext`. Actor and organization identity are therefore not
universal mandatory taxonomy dimensions.

P6-002 does not modify the persisted `AuditEvent` schema for actor-less events.
`TASK-P6-003` will define authentication event production and persistence while
conforming to this taxonomy.

---

## 17. Correlation, Ordering, and Lifecycle

- Correlation identifiers are optional future metadata and are not introduced here.
- `occurred_at` is the recorded event timestamp; global total ordering is not guaranteed.
- Registry order is not event occurrence order.
- Retention, export, archival, and integrity remain future tasks (P6-004 through P6-006).

Event records remain immutable after append.

---

## 18. Extension Workflow

To introduce a future security event type:

1. define the completed security fact;
2. identify the authoritative trigger owner;
3. select one primary category;
4. select one subject domain;
5. define allowed outcomes;
6. define a stable event identifier;
7. define safe metadata allowlisting;
8. register an immutable descriptor;
9. implement one authoritative production path;
10. add duplicate-prevention verification;
11. add compatibility tests;
12. update architecture documentation.

A string constant alone is not sufficient.

---

## 19. Future Phase Boundaries

| Task | Scope |
|------|-------|
| P6-003 | Authentication Security Events production and persistence |
| P6-004 | Audit Retention & Lifecycle |
| P6-005 | Audit Export API |
| P6-006 | Audit Integrity |

Future tasks must extend this registry rather than redefine event identity,
classification, or producer ownership.

---

## 20. Sensitive Data

Auditable security events must never persist passwords, tokens, credentials, raw request
bodies, or authorization headers. Taxonomy classification does not make sensitive values
safe.

Metadata allowlisting remains authoritative for persisted event payloads.
