from __future__ import annotations

from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities import KnowledgeObject
from backend.core.domain.repositories import (
    KnowledgeObjectRelationRepositoryContract,
    KnowledgeObjectRepositoryContract,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories import (
    SQLAlchemyKnowledgeObjectRelationRepository,
    SQLAlchemyKnowledgeObjectRepository,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from tests.contracts.knowledge_object_relation_repository_contract import (
    KnowledgeObjectRelationRepositoryContractSuite,
    create_relation_context,
)
from tests.contracts.knowledge_object_repository_contract import (
    KnowledgeObjectRepositoryContractSuite,
)
from tests.contracts.unit_of_work_contract import UnitOfWorkContractSuite


pytestmark = pytest.mark.db
pytest_plugins = ("tests.infrastructure.db_fixtures",)


class TestSQLAlchemyKnowledgeObjectRepositoryContract(
    KnowledgeObjectRepositoryContractSuite
):
    @pytest.fixture()
    def repository(
        self,
        sqlalchemy_session: Session,
    ) -> KnowledgeObjectRepositoryContract:
        return SQLAlchemyKnowledgeObjectRepository(sqlalchemy_session)


class TestSQLAlchemyKnowledgeObjectRelationRepositoryContract(
    KnowledgeObjectRelationRepositoryContractSuite
):
    @pytest.fixture()
    def relation_context(
        self,
        sqlalchemy_session: Session,
    ) -> tuple[KnowledgeObjectRelationRepositoryContract, KnowledgeObject, KnowledgeObject]:
        source, target = create_relation_context()
        object_repository = SQLAlchemyKnowledgeObjectRepository(sqlalchemy_session)
        object_repository.add(source)
        object_repository.add(target)
        sqlalchemy_session.flush()
        return SQLAlchemyKnowledgeObjectRelationRepository(sqlalchemy_session), source, target


class TestSQLAlchemyUnitOfWorkContract(UnitOfWorkContractSuite):
    @pytest.fixture()
    def unit_of_work_factory(
        self,
        sqlalchemy_session_factory: sessionmaker[Session],
    ) -> Callable[[], UnitOfWorkContract]:
        return lambda: SQLAlchemyUnitOfWork(sqlalchemy_session_factory)
