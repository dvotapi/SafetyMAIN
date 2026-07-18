# TASK-S1-003

## Title

Introduce Domain Exceptions

## Goal

Introduce explicit domain exceptions for Knowledge Object lifecycle and repository operations.

The objective is to make domain failures predictable, typed and independent from infrastructure.

## Create

backend/core/domain/exceptions/base.py
backend/core/domain/exceptions/knowledge_object.py

## Implement

### Base Exception

Create:

SafetyMainDomainError

All domain-specific exceptions shall inherit from it.

### Knowledge Object Exceptions

Create:

KnowledgeObjectNotFound

KnowledgeObjectAlreadyArchived

KnowledgeObjectAlreadyActive

KnowledgeObjectAlreadyDeleted

InvalidKnowledgeObjectStateTransition

KnowledgeObjectVersionConflict

DuplicateKnowledgeObject

## Requirements

Exceptions shall:

- contain a clear human-readable message;
- preserve relevant domain identifiers;
- avoid HTTP status codes;
- avoid database-specific details;
- avoid infrastructure dependencies;
- be safe to catch in the application layer.

KnowledgeObjectNotFound shall contain:

- knowledge_object_id

KnowledgeObjectVersionConflict shall contain:

- knowledge_object_id
- expected_version
- actual_version

InvalidKnowledgeObjectStateTransition shall contain:

- knowledge_object_id
- current_status
- requested_status

## Refactor

Replace generic exceptions in:

- KnowledgeObjectService
- application handlers
- in-memory repository

Use the new domain exceptions where semantically appropriate.

Do not change successful behavior.

Do not add API exception mapping.

## Tests

Add tests verifying:

- correct exception types;
- stored domain context;
- readable messages;
- archive of already archived object fails;
- restore of active object fails;
- missing object raises KnowledgeObjectNotFound;
- version conflict raises KnowledgeObjectVersionConflict if optimistic version checking already exists.

If optimistic version checking does not yet exist, define the exception but do not introduce unrelated version-checking behavior in this task.

All existing tests must continue to pass.

## Acceptance Criteria

- Domain exception hierarchy implemented.
- Generic exceptions removed where applicable.
- Domain and application layers remain infrastructure-independent.
- Existing behavior remains unchanged for successful operations.
- Tests pass.
- Ruff and import validation pass.

## Definition of Done

SafetyMAIN Core exposes a predictable and typed domain error model.
