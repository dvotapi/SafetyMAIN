# Knowledge Object Search

SafetyMAIN Core supports deterministic in-memory structured search for Knowledge Objects.

## Supported Filters

- `organization_id` is required and always enforced.
- `object_type` supports exact matching after normal `KnowledgeObjectType` normalization.
- `status` supports exact lifecycle status matching.
- `metadata_equals` supports exact top-level metadata matching with AND semantics.

## Deleted Objects

If `status` is omitted, search returns `ACTIVE` and `ARCHIVED` objects only. `DELETED` objects are excluded by default.

To search deleted objects, set `status=DELETED` explicitly.

## Metadata Matching

Metadata matching is exact and JSON type-sensitive:

- missing fields do not match;
- nested-path querying is not supported;
- `3` does not match `"3"`;
- `true` does not match `1`.

## Pagination

Filtering is applied first, then deterministic ordering, then pagination.

Results include:

- immutable `items`;
- `total` before pagination;
- `limit`;
- `offset`.

Ordering is by `created_at` ascending, then Knowledge Object ID.

## Limitations

This search does not provide full-text search, fuzzy matching, vector search, relation search, database queries, or external search engine integration.
