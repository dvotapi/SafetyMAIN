from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from backend.core.domain.entities import KnowledgeObject, KnowledgeObjectRelation
from backend.core.domain.exceptions import (
    DuplicateKnowledgeObjectRelation,
    KnowledgeObjectRelationNotFound,
)
from backend.core.domain.repositories import KnowledgeObjectRelationRepositoryContract
from backend.core.domain.value_objects import (
    KnowledgeObjectRelationType,
    OrganizationId,
)
from tests.contracts.knowledge_object_repository_contract import create_knowledge_object


class KnowledgeObjectRelationRepositoryContractSuite:
    @pytest.fixture()
    def relation_context(
        self,
    ) -> tuple[KnowledgeObjectRelationRepositoryContract, KnowledgeObject, KnowledgeObject]:
        raise NotImplementedError

    def test_add_get_duplicate_reverse_and_missing(
        self,
        relation_context: tuple[
            KnowledgeObjectRelationRepositoryContract,
            KnowledgeObject,
            KnowledgeObject,
        ],
    ) -> None:
        repository, source, target = relation_context
        relation = create_relation(source=source, target=target, relation_type="uses")
        duplicate = create_relation(source=source, target=target, relation_type="uses")
        reverse = create_relation(source=target, target=source, relation_type="uses")

        repository.add(relation)
        repository.add(reverse)

        assert repository.get(relation.relation_id) == relation
        assert repository.get(reverse.relation_id) == reverse
        with pytest.raises(DuplicateKnowledgeObjectRelation):
            repository.add(duplicate)
        with pytest.raises(KnowledgeObjectRelationNotFound):
            repository.get(uuid4())

    def test_remove_contract(
        self,
        relation_context: tuple[
            KnowledgeObjectRelationRepositoryContract,
            KnowledgeObject,
            KnowledgeObject,
        ],
    ) -> None:
        repository, source, target = relation_context
        first = create_relation(source=source, target=target, relation_type="uses")
        second = create_relation(source=source, target=target, relation_type="owns")
        repository.add(first)
        repository.add(second)

        repository.remove(first.relation_id)

        with pytest.raises(KnowledgeObjectRelationNotFound):
            repository.get(first.relation_id)
        assert repository.get(second.relation_id) == second
        with pytest.raises(KnowledgeObjectRelationNotFound):
            repository.remove(uuid4())

    def test_exists_contract(
        self,
        relation_context: tuple[
            KnowledgeObjectRelationRepositoryContract,
            KnowledgeObject,
            KnowledgeObject,
        ],
    ) -> None:
        repository, source, target = relation_context
        relation = create_relation(source=source, target=target, relation_type="uses")
        repository.add(relation)

        assert repository.exists(
            relation.organization_id,
            relation.source_object_id,
            relation.target_object_id,
            relation.relation_type,
        )
        assert not repository.exists(
            relation.organization_id,
            relation.target_object_id,
            relation.source_object_id,
            relation.relation_type,
        )
        assert not repository.exists(
            relation.organization_id,
            relation.source_object_id,
            relation.target_object_id,
            KnowledgeObjectRelationType(value="owns"),
        )
        assert not repository.exists(
            OrganizationId(value=uuid4()),
            relation.source_object_id,
            relation.target_object_id,
            relation.relation_type,
        )

    def test_traversal_contract(
        self,
        relation_context: tuple[
            KnowledgeObjectRelationRepositoryContract,
            KnowledgeObject,
            KnowledgeObject,
        ],
    ) -> None:
        repository, source, target = relation_context
        created_at = datetime.now(UTC)
        later = create_relation(
            source=source,
            target=target,
            relation_id=UUID("00000000-0000-0000-0000-000000000002"),
            relation_type="uses",
            created_at=created_at,
        )
        earlier = create_relation(
            source=source,
            target=target,
            relation_id=UUID("00000000-0000-0000-0000-000000000001"),
            relation_type="owns",
            created_at=created_at,
        )
        repository.add(later)
        repository.add(earlier)

        outgoing = repository.outgoing(source.header.organization_id, source.header.id)
        incoming = repository.incoming(target.header.organization_id, target.header.id)

        assert outgoing == (earlier, later)
        assert incoming == (earlier, later)
        assert repository.outgoing(
            source.header.organization_id,
            source.header.id,
            KnowledgeObjectRelationType(value="uses"),
        ) == (later,)
        assert repository.incoming(
            target.header.organization_id,
            target.header.id,
            KnowledgeObjectRelationType(value="missing"),
        ) == ()
        assert repository.outgoing(OrganizationId(value=uuid4()), source.header.id) == ()
        with pytest.raises(AttributeError):
            outgoing.append(later)  # type: ignore[attr-defined]


def create_relation(
    *,
    source: KnowledgeObject,
    target: KnowledgeObject,
    relation_id: UUID | None = None,
    relation_type: str = "uses",
    created_at: datetime | None = None,
) -> KnowledgeObjectRelation:
    return KnowledgeObjectRelation(
        relation_id=relation_id or uuid4(),
        organization_id=source.header.organization_id,
        source_object_id=source.header.id,
        target_object_id=target.header.id,
        relation_type=KnowledgeObjectRelationType(value=relation_type),
        created_at=created_at or datetime.now(UTC),
    )


def create_relation_context() -> tuple[KnowledgeObject, KnowledgeObject]:
    organization_id = OrganizationId(value=uuid4())
    return (
        create_knowledge_object(organization_id=organization_id),
        create_knowledge_object(organization_id=organization_id),
    )
