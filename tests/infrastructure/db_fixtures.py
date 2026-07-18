from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(scope="module")
def database_url() -> str:
    if os.environ.get("SAFETYMAIN_RUN_DB_TESTS") != "1":
        pytest.skip("Set SAFETYMAIN_RUN_DB_TESTS=1 to run PostgreSQL tests.")

    value = os.environ.get("DATABASE_URL")
    if not value:
        pytest.skip("DATABASE_URL is required to run PostgreSQL tests.")

    return value


@pytest.fixture()
def migrated_engine(database_url: str) -> Iterator[Engine]:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        yield engine
    finally:
        engine.dispose()
        command.downgrade(config, "base")


@pytest.fixture()
def sqlalchemy_session(migrated_engine: Engine) -> Iterator[Session]:
    session_factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def sqlalchemy_session_factory(migrated_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=migrated_engine, expire_on_commit=False)
