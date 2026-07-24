# Hazards API

Base path: `/api/v1/hazards`

## Endpoints

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/hazards` | `hazard:create` |
| GET | `/api/v1/hazards` | `hazard:read` |
| GET | `/api/v1/hazards/{hazard_id}` | `hazard:read` |
| PATCH | `/api/v1/hazards/{hazard_id}` | `hazard:update` |
| POST | `/api/v1/hazards/{hazard_id}/activate` | `hazard:activate` |
| POST | `/api/v1/hazards/{hazard_id}/archive` | `hazard:archive` |
| POST | `/api/v1/hazards/{hazard_id}/restore` | `hazard:restore` |

There is no DELETE endpoint. Archiving is soft retention.

## Create body

`code`, `title`, `description`, `category`, `safety_directions`, `source`,
`affected_subjects`, optional references, optional `identified_at`, optional
`extension_references`.

Organization ownership always comes from tenant context.

## List filters

`status`, `category`, `safety_direction`, `source`, `affected_subject`,
`identified_from/to`, `created_from/to`, `search`, `include_archived`,
`offset`, `limit`.

Default sort: `created_at DESC, id DESC`. Archived hazards are excluded unless
`include_archived=true`.

## Errors

| HTTP | Typical cause |
|---|---|
| 400 | malformed request |
| 401 | authentication required |
| 403 | permission denied |
| 404 | missing or cross-tenant hazard |
| 409 | duplicate code or version conflict |
| 422 | invalid lifecycle/domain rule |

Optimistic concurrency requires `expected_version` on update/lifecycle calls.
