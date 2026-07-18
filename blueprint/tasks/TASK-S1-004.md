# TASK-S1-004

## Title

Review and Normalize Repository and Unit of Work Contracts

## Goal

Stabilize persistence-facing contracts before implementing additional use cases and infrastructure adapters.

This task must not add new business capabilities.

## Scope

Review:

- KnowledgeObjectRepositoryContract
- UnitOfWorkContract
- in-memory repository implementation
- in-memory Unit of Work implementation
- application handlers using these contracts

## Repository Contract

Normalize the public API.

Expected operations:

- add(knowledge_object)
- get(knowledge_object_id)
- update(knowledge_object)
- history(knowledge_object_id)
- archive(knowledge_object)
- restore(knowledge_object)

Review whether `archive()` and `restore()` are necessary repository operations.

Preferred design:

- lifecycle transitions belong to the Domain Service;
- repository persists the resulting KnowledgeObject through `update()`;
- repository should not contain business-specific lifecycle behavior.

If current `archive()` and `restore()` methods only duplicate `update()`, remove them from the contract and adapter.

## Return Semantics

Define consistent behavior:

- `get()` returns a KnowledgeObject or raises KnowledgeObjectNotFound;
- `add()` returns None;
- `update()` returns None;
- `history()` returns an immutable sequence of historical KnowledgeObject versions;
- repository methods must not return infrastructure-specific values.

Do not mix `Optional` returns with `NotFound` exceptions.

## Version History

Clarify and test:

- current version is returned by `get()`;
- `history()` contains previous immutable versions only;
- history ordering is deterministic;
- define ordering as oldest-to-newest;
- returned history cannot mutate repository state.

## Unit of Work Contract

Review and normalize:

- repository access;
- commit();
- rollback();
- context-manager behavior, if already implemented.

Preferred API:

```python
class UnitOfWorkContract(Protocol):
    knowledge_objects: KnowledgeObjectRepositoryContract

    def commit(self) -> None: ...
    def rollback(self) -> None: ...

    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type, exc_value, traceback) -> None: ...
```
