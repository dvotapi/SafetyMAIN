# Timeline and Activity Feed

Status: Active  
Date: 2026-07-25  
Task: TASK-P9-001

Related: [PageTemplates.md](PageTemplates.md) · [StatusLanguage.md](StatusLanguage.md) · [AdministrativeAuditLog.md](../architecture/AdministrativeAuditLog.md)

---

## 1. Timeline

Standard history visualization on Object Pages.

### Supported item types

| Type | Examples |
|------|----------|
| Status change | Draft → Planned |
| Audit | `safety.risk_control.verified_effective` |
| Comment | User note |
| Attachment / evidence ref | Evidence added (reference, not binary preview required) |
| System event | Materialized from assessment |
| User event | Owner assigned |

### Anatomy

```text
●  12:40  Maria K.  Status changed
│         Planned → In Implementation
│
●  11:02  System    Evidence added
│         INV-evidence-19
```

| Element | Rule |
|---------|------|
| Axis | Vertical; newest-first default (toggle oldest-first optional) |
| Actor | Avatar + name or “System” |
| Timestamp | Relative + absolute on hover / title |
| Body | Plain language; link related objects |
| Grouping | Optional by day headers |

### Rules

1. Timeline is append-oriented in presentation; corrections (future) appear as new events, not silent edits.
2. Do not expose raw hash-chain internals unless an investigation view explicitly requires them.
3. Tenant-scoped: only events for the current org/object.

---

## 2. Activity Feed

Cross-object or page-level stream (Dashboard, Overview, Object Activity tab).

### Capabilities

| Feature | Rule |
|---------|------|
| Filters | Type, actor, date range, object type |
| Actor | Always shown |
| Timestamp | Required |
| Object links | Code + title → Object Page |
| Grouping | By day; collapse high-volume system noise |

### Relationship to Timeline

| View | Scope |
|------|-------|
| Timeline | Single object history |
| Activity Feed | Stream across objects or org |

Shared presentational atoms (`ActivityItem`); different data queries.

---

## 3. Components

`Timeline`, `TimelineItem`, `ActivityFeed`, `ActivityItem`, `ActivityFilters`.
