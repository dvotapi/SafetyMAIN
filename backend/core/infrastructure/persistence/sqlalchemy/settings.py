from __future__ import annotations

import os
from collections.abc import Mapping


DATABASE_URL_ENV_NAME = "DATABASE_URL"


class DatabaseConfigurationError(RuntimeError):
    """Raised when database infrastructure is initialized without configuration."""


def get_database_url(
    environment: Mapping[str, str] | None = None,
) -> str:
    if environment is None:
        source = os.environ
    else:
        source = environment
    database_url = source.get(DATABASE_URL_ENV_NAME)

    if not database_url:
        raise DatabaseConfigurationError(
            f"{DATABASE_URL_ENV_NAME} is required to initialize database infrastructure."
        )

    return database_url
