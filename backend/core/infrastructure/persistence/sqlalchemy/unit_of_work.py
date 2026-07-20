from __future__ import annotations

from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.repositories import (
    KnowledgeObjectRelationRepositoryContract,
    KnowledgeObjectRepositoryContract,
)
from backend.core.infrastructure.persistence.sqlalchemy.repositories import (
    SQLAlchemyKnowledgeObjectRelationRepository,
    SQLAlchemyKnowledgeObjectRepository,
)


class SQLAlchemyUnitOfWork(UnitOfWorkContract):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._knowledge_objects: SQLAlchemyKnowledgeObjectRepository | None = None
        self._relations: SQLAlchemyKnowledgeObjectRelationRepository | None = None
        self._committed = False
        self._rolled_back = False

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("SQLAlchemyUnitOfWork has not been entered.")

        return self._session

    @property
    def knowledge_objects(self) -> KnowledgeObjectRepositoryContract:
        if self._knowledge_objects is None:
            raise RuntimeError("SQLAlchemyUnitOfWork has not been entered.")

        return self._knowledge_objects

    @property
    def relations(self) -> KnowledgeObjectRelationRepositoryContract:
        if self._relations is None:
            raise RuntimeError("SQLAlchemyUnitOfWork has not been entered.")

        return self._relations

    def commit(self) -> None:
        if self._committed:
            return

        self.session.commit()
        self._committed = True

    def rollback(self) -> None:
        if self._rolled_back:
            return

        if self._session is not None:
            self._session.rollback()

        self._rolled_back = True

    def __enter__(self) -> SQLAlchemyUnitOfWork:
        self._session = self._session_factory()
        self._knowledge_objects = SQLAlchemyKnowledgeObjectRepository(self._session)
        self._relations = SQLAlchemyKnowledgeObjectRelationRepository(self._session)
        self._committed = False
        self._rolled_back = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        try:
            if exc_type is not None or not self._committed:
                self.rollback()
        finally:
            if self._session is not None:
                self._session.close()
                self._session = None
                self._knowledge_objects = None
                self._relations = None

        return False
