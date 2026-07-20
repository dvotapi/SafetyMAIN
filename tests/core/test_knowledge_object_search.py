from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from backend.core.application.handlers.search_knowledge_objects import (
    SearchKnowledgeObjectsHandler,
)
from backend.core.application.queries.search_knowledge_objects import (
    SearchKnowledgeObjectsQuery,
)
from backend.core.domain.entities.knowledge_object import (
    KnowledgeObject,
    KnowledgeObjectHeader,
    KnowledgeObjectStatus,
)
from backend.core.domain.value_objects import KnowledgeObjectType, OrganizationId
from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork


def test_search_by_organization_only_excludes_draft_and_deleted_by_default() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    active_object = _add_object(unit_of_work, organization_id, status=KnowledgeObjectStatus.ACTIVE)
    archived_object = _add_object(
        unit_of_work,
        organization_id,
        status=KnowledgeObjectStatus.ARCHIVED,
    )
    _add_object(unit_of_work, organization_id, status=KnowledgeObjectStatus.DRAFT)
    _add_object(unit_of_work, organization_id, status=KnowledgeObjectStatus.DELETED)

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=organization_id)
    )

    assert result.items == (active_object, archived_object)
    assert result.total == 2


def test_search_preserves_organization_isolation() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    other_organization_id = OrganizationId(value=uuid4())
    expected_object = _add_object(unit_of_work, organization_id)
    _add_object(unit_of_work, other_organization_id)

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=organization_id)
    )

    assert result.items == (expected_object,)


def test_search_by_knowledge_object_type() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    expected_object = _add_object(unit_of_work, organization_id, object_type="Instruction")
    _add_object(unit_of_work, organization_id, object_type="Risk")

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            object_type=KnowledgeObjectType(value=" instruction "),
        )
    )

    assert result.items == (expected_object,)


def test_search_by_lifecycle_status() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    expected_object = _add_object(
        unit_of_work,
        organization_id,
        status=KnowledgeObjectStatus.DRAFT,
    )
    _add_object(unit_of_work, organization_id, status=KnowledgeObjectStatus.ACTIVE)

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            status=KnowledgeObjectStatus.DRAFT,
        )
    )

    assert result.items == (expected_object,)


def test_explicit_search_for_deleted_objects() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    expected_object = _add_object(
        unit_of_work,
        organization_id,
        status=KnowledgeObjectStatus.DELETED,
    )

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            status=KnowledgeObjectStatus.DELETED,
        )
    )

    assert result.items == (expected_object,)


def test_search_by_one_metadata_field() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    expected_object = _add_object(
        unit_of_work,
        organization_id,
        payload={"department": "production"},
    )
    _add_object(unit_of_work, organization_id, payload={"department": "maintenance"})

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            metadata_equals={"department": "production"},
        )
    )

    assert result.items == (expected_object,)


def test_search_by_multiple_metadata_fields_uses_and_semantics() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    expected_object = _add_object(
        unit_of_work,
        organization_id,
        payload={"department": "production", "approved": True},
    )
    _add_object(
        unit_of_work,
        organization_id,
        payload={"department": "production", "approved": False},
    )

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            metadata_equals={"department": "production", "approved": True},
        )
    )

    assert result.items == (expected_object,)


def test_missing_metadata_field_does_not_match() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    _add_object(unit_of_work, organization_id, payload={"department": "production"})

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            metadata_equals={"approved": True},
        )
    )

    assert result.items == ()
    assert result.total == 0


def test_metadata_matching_is_type_sensitive() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    _add_object(unit_of_work, organization_id, payload={"risk_level": 3})

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            metadata_equals={"risk_level": "3"},
        )
    )

    assert result.items == ()


def test_boolean_and_integer_values_are_not_equal() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    expected_object = _add_object(unit_of_work, organization_id, payload={"approved": True})
    _add_object(unit_of_work, organization_id, payload={"approved": 1})

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            metadata_equals={"approved": True},
        )
    )

    assert result.items == (expected_object,)


def test_combined_type_status_and_metadata_filters() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    expected_object = _add_object(
        unit_of_work,
        organization_id,
        object_type="Instruction",
        status=KnowledgeObjectStatus.ARCHIVED,
        payload={"department": "production"},
    )
    _add_object(
        unit_of_work,
        organization_id,
        object_type="Instruction",
        status=KnowledgeObjectStatus.ACTIVE,
        payload={"department": "production"},
    )

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            object_type=KnowledgeObjectType(value="instruction"),
            status=KnowledgeObjectStatus.ARCHIVED,
            metadata_equals={"department": "production"},
        )
    )

    assert result.items == (expected_object,)


def test_no_matches_returns_immutable_empty_sequence() -> None:
    result = SearchKnowledgeObjectsHandler(InMemoryUnitOfWork()).handle(
        SearchKnowledgeObjectsQuery(organization_id=OrganizationId(value=uuid4()))
    )

    assert result.items == ()
    with pytest.raises(AttributeError):
        result.items.append("item")  # type: ignore[attr-defined]


def test_search_ordering_is_deterministic() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    now = datetime.now(UTC)
    later_object = _add_object(
        unit_of_work,
        organization_id,
        object_id=UUID("00000000-0000-0000-0000-000000000002"),
        created_at=now,
    )
    earlier_object = _add_object(
        unit_of_work,
        organization_id,
        object_id=UUID("00000000-0000-0000-0000-000000000001"),
        created_at=now,
    )

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=organization_id)
    )

    assert result.items == (earlier_object, later_object)


def test_search_pagination_first_and_subsequent_pages() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    objects = [
        _add_object(unit_of_work, organization_id, created_at=datetime.now(UTC) + timedelta(seconds=index))
        for index in range(3)
    ]

    first_page = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=organization_id, limit=2, offset=0)
    )
    second_page = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=organization_id, limit=2, offset=2)
    )

    assert first_page.items == tuple(objects[:2])
    assert first_page.total == 3
    assert second_page.items == (objects[2],)
    assert second_page.total == 3


def test_search_offset_beyond_result_count_returns_empty_page() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    _add_object(unit_of_work, organization_id)

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=organization_id, limit=10, offset=99)
    )

    assert result.items == ()
    assert result.total == 1


def test_invalid_limit_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SearchKnowledgeObjectsHandler(InMemoryUnitOfWork()).handle(
            SearchKnowledgeObjectsQuery(
                organization_id=OrganizationId(value=uuid4()),
                limit=0,
            )
        )


def test_limit_above_maximum_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SearchKnowledgeObjectsHandler(InMemoryUnitOfWork()).handle(
            SearchKnowledgeObjectsQuery(
                organization_id=OrganizationId(value=uuid4()),
                limit=101,
            )
        )


def test_negative_offset_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SearchKnowledgeObjectsHandler(InMemoryUnitOfWork()).handle(
            SearchKnowledgeObjectsQuery(
                organization_id=OrganizationId(value=uuid4()),
                offset=-1,
            )
        )


def test_empty_metadata_key_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SearchKnowledgeObjectsHandler(InMemoryUnitOfWork()).handle(
            SearchKnowledgeObjectsQuery(
                organization_id=OrganizationId(value=uuid4()),
                metadata_equals={" ": "value"},
            )
        )


def test_read_handler_does_not_commit() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    _add_object(unit_of_work, organization_id)
    unit_of_work.committed = False

    SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=organization_id)
    )

    assert unit_of_work.committed is False


def test_returned_items_cannot_mutate_repository_state() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    expected_object = _add_object(unit_of_work, organization_id)
    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=organization_id)
    )

    with pytest.raises(AttributeError):
        result.items.append(expected_object)  # type: ignore[attr-defined]

    next_result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(organization_id=organization_id)
    )
    assert next_result.items == (expected_object,)


def test_include_deleted_without_status_includes_deleted_objects() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    active_object = _add_object(unit_of_work, organization_id, status=KnowledgeObjectStatus.ACTIVE)
    archived_object = _add_object(
        unit_of_work,
        organization_id,
        status=KnowledgeObjectStatus.ARCHIVED,
    )
    deleted_object = _add_object(
        unit_of_work,
        organization_id,
        status=KnowledgeObjectStatus.DELETED,
    )
    _add_object(unit_of_work, organization_id, status=KnowledgeObjectStatus.DRAFT)

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            include_deleted=True,
        )
    )

    assert result.items == (active_object, archived_object, deleted_object)
    assert result.total == 3


def test_include_deleted_false_excludes_deleted_even_when_status_omitted() -> None:
    unit_of_work = InMemoryUnitOfWork()
    organization_id = OrganizationId(value=uuid4())
    active_object = _add_object(unit_of_work, organization_id, status=KnowledgeObjectStatus.ACTIVE)
    _add_object(unit_of_work, organization_id, status=KnowledgeObjectStatus.DELETED)

    result = SearchKnowledgeObjectsHandler(unit_of_work).handle(
        SearchKnowledgeObjectsQuery(
            organization_id=organization_id,
            include_deleted=False,
        )
    )

    assert result.items == (active_object,)
    assert result.total == 1


def _add_object(
    unit_of_work: InMemoryUnitOfWork,
    organization_id: OrganizationId,
    *,
    object_id: UUID | None = None,
    object_type: str = "Object",
    status: KnowledgeObjectStatus = KnowledgeObjectStatus.ACTIVE,
    created_at: datetime | None = None,
    payload: dict[str, object] | None = None,
) -> KnowledgeObject:
    created = created_at or datetime.now(UTC)
    knowledge_object = KnowledgeObject(
        header=KnowledgeObjectHeader(
            id=object_id or uuid4(),
            object_type=object_type,
            organization_id=organization_id,
            status=status,
            version=1,
            created_at=created,
            updated_at=created,
        ),
        payload=payload or {},
    )
    unit_of_work.knowledge_objects.add(knowledge_object)
    return knowledge_object
