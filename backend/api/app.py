from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from backend.api.constants import API_V1_PREFIX
from backend.api.exception_handlers import register_exception_handlers
from backend.api.logging import configure_logging
from backend.api.middleware import RequestIdMiddleware
from backend.api.routers import auth as auth_router
from backend.api.routers import knowledge_objects as knowledge_objects_router
from backend.api.routers import relations as relations_router
from backend.api.routers import system as system_router
from backend.bootstrap.container import AppContainer, create_container
from backend.bootstrap.settings import AppSettings, load_settings


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup intentionally does not connect, migrate, or create schema.
    yield
    container: AppContainer = app.state.container
    container.dispose()


def create_app(
    settings: AppSettings | None = None,
    *,
    container: AppContainer | None = None,
) -> FastAPI:
    """Create an isolated FastAPI application instance.

    Importing this module and calling ``create_app`` must not:
    - connect to PostgreSQL;
    - open a SQLAlchemy Session;
    - create tables;
    - apply migrations.
    """

    configure_logging()
    resolved_settings = settings if settings is not None else load_settings()
    resolved_container = (
        container if container is not None else create_container(resolved_settings)
    )

    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=_lifespan,
    )
    application.state.settings = resolved_settings
    application.state.container = resolved_container

    application.add_middleware(RequestIdMiddleware)

    if resolved_settings.cors_allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_settings.cors_allowed_origins),
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(application)

    def custom_openapi() -> dict[str, object]:
        if application.openapi_schema:
            return application.openapi_schema

        schema = get_openapi(
            title=application.title,
            version=application.version,
            routes=application.routes,
        )
        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        application.openapi_schema = schema
        return schema

    application.openapi = custom_openapi

    api_v1 = APIRouter(prefix=API_V1_PREFIX)
    api_v1.include_router(system_router.router)
    api_v1.include_router(auth_router.router)
    api_v1.include_router(knowledge_objects_router.router)
    api_v1.include_router(relations_router.router)
    application.include_router(api_v1)

    return application


# Thin default instance for Uvicorn. Construction has no external side effects.
app = create_app()
