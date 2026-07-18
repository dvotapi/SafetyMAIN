from __future__ import annotations

from collections.abc import Callable

import pytest

from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities import KnowledgeObject
from backend.core.domain.repositories import (
    KnowledgeObjectRelationRepositoryContract,
    KnowledgeObjectRepositoryContract,
)
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryKnowledgeObjectRelationRepository,
    InMemoryKnowledgeObjectRepository,
    InMemoryUnitOfWork,
)
from tests.contracts.knowledge_object_relation_repository_contract import (
    KnowledgeObjectRelationRepositoryContractSuite,
    create_relation_context,
)
from tests.contracts.knowledge_object_repository_contract import (
    KnowledgeObjectRepositoryContractSuite,
)
from tests.contracts.unit_of_work_contract import UnitOfWorkContractSuite


class TestInMemoryKnowledgeObjectRepositoryContract(
    KnowledgeObjectRepositoryContractSuite
):
    @pytest.fixture()
    def repository(self) -> KnowledgeObjectRepositoryContract:
        return InMemoryKnowledgeObjectRepository()


class TestInMemoryKnowledgeObjectRelationRepositoryContract(
    KnowledgeObjectRelationRepositoryContractSuite
):
    @pytest.fixture()
    def relation_context(
        self,
    ) -> tuple[KnowledgeObjectRelationRepositoryContract, KnowledgeObject, KnowledgeObject]:
        source, target = create_relation_context()
        return InMemoryKnowledgeObjectRelationRepository(), source, target


class TestInMemoryUnitOfWorkContract(UnitOfWorkContractSuite):
    @pytest.fixture()
    def unit_of_work_factory(self) -> Callable[[], UnitOfWorkContract]:
        knowledge_objects = InMemoryKnowledgeObjectRepository()
        relations = InMemoryKnowledgeObjectRelationRepository()

        return lambda: InMemoryUnitOfWork(
            knowledge_objects=knowledge_objects,
            relations=relations,
        )
