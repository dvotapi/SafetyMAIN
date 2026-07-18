from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)


class TrackingSession(Session):
    was_closed = False

    def close(self) -> None:
        self.was_closed = True
        super().close()


def test_session_is_created_on_enter_and_closed_on_exit() -> None:
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine, class_=TrackingSession)
    unit_of_work = SQLAlchemyUnitOfWork(session_factory)

    with unit_of_work as active_unit_of_work:
        session = active_unit_of_work.session
        assert isinstance(session, TrackingSession)
        assert session.was_closed is False

    assert session.was_closed is True
