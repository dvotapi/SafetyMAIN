from __future__ import annotations

import importlib

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.infrastructure.persistence.sqlalchemy.engine import (
    create_engine,
    create_session,
    create_session_factory,
)
from backend.core.infrastructure.persistence.sqlalchemy.settings import (
    DatabaseConfigurationError,
    get_database_url,
)


def test_get_database_url_reads_explicit_environment() -> None:
    database_url = "postgresql+psycopg://user:password@localhost:5432/database"

    assert get_database_url({"DATABASE_URL": database_url}) == database_url


def test_missing_database_url_fails_only_when_requested() -> None:
    with pytest.raises(DatabaseConfigurationError):
        get_database_url({})


def test_engine_creation_is_explicit() -> None:
    engine = create_engine("postgresql+psycopg://user:password@localhost:5432/database")

    assert isinstance(engine, Engine)


def test_session_factory_can_be_constructed() -> None:
    engine = create_engine("postgresql+psycopg://user:password@localhost:5432/database")
    session_factory = create_session_factory(engine)

    assert isinstance(session_factory, sessionmaker)


def test_session_can_be_constructed_without_connecting() -> None:
    engine = create_engine("postgresql+psycopg://user:password@localhost:5432/database")
    session_factory = create_session_factory(engine)

    session = create_session(session_factory)

    assert isinstance(session, Session)
    session.close()


def test_importing_persistence_modules_does_not_connect(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("create_engine must not be called during import")

    monkeypatch.setattr(
        "sqlalchemy.create_engine",
        fail_if_called,
    )

    importlib.reload(
        importlib.import_module(
            "backend.core.infrastructure.persistence.sqlalchemy.settings"
        )
    )
    importlib.reload(
        importlib.import_module("backend.core.infrastructure.persistence.sqlalchemy.base")
    )
