from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from alembic import command


def _require_database_url() -> str:
    if os.environ.get("SAFETYMAIN_RUN_DB_TESTS") != "1":
        pytest.skip("Set SAFETYMAIN_RUN_DB_TESTS=1 to run PostgreSQL tests.")

    value = os.environ.get("DATABASE_URL")
    if not value:
        pytest.fail(
            "SAFETYMAIN_RUN_DB_TESTS=1 requires DATABASE_URL; refusing to silently skip."
        )
    return value


@pytest.fixture(scope="module")
def database_url() -> str:
    return _require_database_url()


@pytest.fixture()
def migrated_engine(database_url: str) -> Iterator[Engine]:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — convert connectivity errors into hard failures
        engine.dispose()
        pytest.fail(
            "SAFETYMAIN_RUN_DB_TESTS=1 but PostgreSQL is unreachable via DATABASE_URL: "
            f"{type(exc).__name__}: {exc}"
        )

    command.downgrade(config, "base")
    command.upgrade(config, "head")

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
