from __future__ import annotations

from sqlalchemy import Engine, create_engine as sqlalchemy_create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.infrastructure.persistence.sqlalchemy.settings import get_database_url


def create_engine(database_url: str | None = None) -> Engine:
    return sqlalchemy_create_engine(database_url or get_database_url())


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_session(session_factory: sessionmaker[Session]) -> Session:
    return session_factory()
