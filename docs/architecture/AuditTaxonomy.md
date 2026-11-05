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

## Compliance shelf events (TASK-P11-012)

Category `compliance`, subject domain `SHELF`. Descriptors live in
`backend/core/domain/security_events/families/compliance.py` (via the
`subject_domain` parameter of `_compliance_descriptor`).

| Event type | Outcome | Resource |
|---|---|---|
| `compliance.place.created` | success/failure | SHELF_PLACE |
| `compliance.place.updated` | success/failure | SHELF_PLACE |
| `compliance.place.excluded` | success/failure | SHELF_PLACE |
| `compliance.place.restored` | success/failure | SHELF_PLACE |
| `compliance.place.confirmed` | success/failure | SHELF_PLACE |
| `compliance.place.linked` | success/failure | SHELF_PLACE |
| `compliance.place.unlinked` | success/failure | SHELF_PLACE |
| `compliance.section.created` | success/failure | SHELF_SECTION |
| `compliance.section.updated` | success/failure | SHELF_SECTION |
| `compliance.shelf.imported` | success/failure | SHELF (emitted by the phase 3 import) |

Metadata of place events: `slot_id`, `slot_code`, `section_code`, `previous_status`,
`new_status` (curated status), `expected_version`, `resulting_version`. Some events add
more:

- `updated`: `changed_fields`;
- `excluded`: `reason` and `comment` (≤ 1000 characters, required by TASK-P11-012);
- `linked`, `unlinked`: `document_id` and `document_code`.

Bulk exclusion records one event per place. Section events carry `section_id`,
`section_code`, `expected_version`, `resulting_version`, `changed_fields` and, for
subsection changes, `subsection_code`. Developing a document from a place records
`compliance.document.created` and `compliance.place.linked` in one transaction.

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
