from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.bootstrap.settings import AppSettings
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.infrastructure.persistence.sqlalchemy.engine import (
    create_engine,
    create_session_factory,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)

UowFactory = Callable[[], UnitOfWorkContract]
ReadinessCheck = Callable[[], None]


@dataclass(slots=True)
class AppContainer:
    """Explicit composition root for production infrastructure wiring.

    Intentionally not a service locator: callers receive this object through
    application state / FastAPI dependencies rather than a hidden global.
    """

    settings: AppSettings
    engine: Engine | None
    session_factory: sessionmaker[Session] | None
    uow_factory: UowFactory
    readiness_check: ReadinessCheck

    def dispose(self) -> None:
        if self.engine is not None:
            self.engine.dispose()


def create_container(settings: AppSettings) -> AppContainer:
    """Assemble infrastructure dependencies without connecting to PostgreSQL.

    ``create_engine`` is lazy: no network I/O occurs until a connection is used.
    """

    engine: Engine | None = None
    session_factory: sessionmaker[Session] | None = None

    if settings.database_url:
        engine = create_engine(settings.database_url)
        session_factory = create_session_factory(engine)

    def uow_factory() -> UnitOfWorkContract:
        if session_factory is None:
            raise RuntimeError("Database is not configured.")
        return SQLAlchemyUnitOfWork(session_factory)

    def readiness_check() -> None:
        if engine is None:
            raise RuntimeError("Database is not configured.")
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        uow_factory=uow_factory,
        readiness_check=readiness_check,
    )
