# Document Types API

Organization-scoped catalog of compliance document types (TASK-P11-001). Served under
`/api/v1/document-types`. Permission `compliance_document:read` is required and
cross-tenant access is masked as 404.

Types are seeded per organization by `scripts/seed_document_types.py` (23 default
entries covering local acts, briefings, orders, employee permits, journals and training
documents). The catalog is read-only via API; types are created by the seed script or
future admin flows.

## `GET /document-types` — `list_document_types`

Query parameters: `include_inactive` (bool, default `false`).

Response:

```json
{
  "items": [
    {
      "id": "<uuid>",
      "organization_id": "<uuid>",
      "code": "iot_profession",
      "title_ru": "ИОТ по профессии",
      "safety_domain": "occupational",
      "subject_kind": "organization",
      "review_period_months": 60,
      "validity_months": null,
      "periodicity_months": null,
      "warning_thresholds_days": [90, 30, 14, 7],
      "requires_acknowledgement": false,
      "requires_approval_order": true,
      "legal_basis": "...",
      "legal_basis_reference": "...",
      "is_active": true,
      "created_at": "<iso datetime>",
      "updated_at": "<iso datetime>"
    }
  ]
}
```

A type carries at most one period: `review_period_months` for planned review (local
acts), `validity_months` for employee permits, or `periodicity_months` for recurring
briefings. `warning_thresholds_days` drives `is_review_due` on documents of that type.

## Errors

| HTTP | Code | When |
|---|---|---|
| 403 | `permission_denied` | Caller lacks `compliance_document:read` |
| 404 | `document_type_not_found` | Reference from another endpoint; this list itself
returns `{items: []}` when nothing is seeded |
