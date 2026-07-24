# Audit Taxonomy

Status: Extended in TASK-P8-002 / TASK-P8-003

## Safety hazard events

Preferred identifiers (category.subject.action):

| Event type | Outcome | Resource |
|---|---|---|
| `safety.hazard.created` | success/failure | HAZARD |
| `safety.hazard.updated` | success/failure | HAZARD |
| `safety.hazard.activated` | success/failure | HAZARD |
| `safety.hazard.archived` | success/failure | HAZARD |
| `safety.hazard.restored` | success/failure | HAZARD |

## Safety risk assessment events

| Event type | Outcome | Resource |
|---|---|---|
| `safety.risk.created` | success/failure | RISK |
| `safety.risk.updated` | success/failure | RISK |
| `safety.risk.approved` | success/failure | RISK |
| `safety.risk.superseded` | success/failure | RISK |
| `safety.risk.archived` | success/failure | RISK |

Descriptors live in `backend/core/domain/security_events/families/safety.py` and
are registered in the published security event registry alongside administrative,
authentication, and authorization families.

## Metadata guidance

Include:

- `hazard_id`, `hazard_code`
- `risk_id`, `risk_code`, `assessment_profile`
- `previous_status`, `new_status` for lifecycle events
- `category`, `safety_directions`
- `inherent_level`, `residual_level`
- `reason` for archive/restore

Avoid storing long free-text descriptions in audit metadata.

Integrity continues to use the existing tamper-evident audit chain.
