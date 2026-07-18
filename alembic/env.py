from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.core.infrastructure.persistence.sqlalchemy.base import Base
from backend.core.infrastructure.persistence.sqlalchemy.models import (
    KnowledgeObjectModel,
    KnowledgeObjectRelationModel,
    KnowledgeObjectVersionModel,
)
from backend.core.infrastructure.persistence.sqlalchemy.settings import (
    DATABASE_URL_ENV_NAME,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_alembic_configuration() -> dict[str, str]:
    configuration = config.get_section(config.config_ini_section, {})

    database_url = os.environ.get(DATABASE_URL_ENV_NAME)
    if database_url:
        configuration["sqlalchemy.url"] = database_url

    if config.cmd_opts is not None:
        x_arguments = context.get_x_argument(as_dictionary=True)
        x_database_url = x_arguments.get(DATABASE_URL_ENV_NAME)
        if x_database_url:
            configuration["sqlalchemy.url"] = x_database_url

    return configuration


def run_migrations_offline() -> None:
    configuration = _get_alembic_configuration()
    context.configure(
        url=configuration["sqlalchemy.url"],
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = _get_alembic_configuration()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


__all__ = [
    "KnowledgeObjectModel",
    "KnowledgeObjectRelationModel",
    "KnowledgeObjectVersionModel",
    "target_metadata",
]
