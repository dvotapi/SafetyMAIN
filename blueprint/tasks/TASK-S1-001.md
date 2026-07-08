# TASK-S1-001

## Title

Introduce Domain Value Objects

---

## Goal

Replace primitive domain types with explicit Value Objects.

The objective is to improve type safety, readability and domain expressiveness.

---

## Create

backend/core/domain/value_objects/

Create:

knowledge_object_id.py

organization_id.py

knowledge_object_type.py

knowledge_object_version.py

---

## Requirements

Use Pydantic v2 where appropriate.

Value Objects shall be immutable.

Each Value Object encapsulates validation.

Examples:

KnowledgeObjectId

- wraps UUID

OrganizationId

- wraps UUID

KnowledgeObjectVersion

- integer >= 1

KnowledgeObjectType

- non-empty string
- normalized to lowercase

---

## Refactor

Update KnowledgeObjectHeader to use the new Value Objects instead of primitive UUID, str and int.

Do not change public behavior.

---

## Tests

Add unit tests for every Value Object.

Update existing tests if required.

All existing integration tests must continue to pass.

---

## Acceptance Criteria

✓ Primitive UUID usage removed from domain model where applicable.

✓ Primitive version integer replaced.

✓ Object type validation centralized.

✓ Tests pass.

✓ No infrastructure dependencies.
