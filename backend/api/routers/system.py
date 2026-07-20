from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_readiness_check, get_settings
from backend.api.exception_handlers import ServiceNotReadyError
from backend.api.openapi import READINESS_ERROR_RESPONSES, success_response
from backend.api.operation_ids import HEALTH, READINESS
from backend.api.schemas.system import HealthResponse, ReadyResponse
from backend.bootstrap.container import ReadinessCheck
from backend.bootstrap.settings import AppSettings

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    operation_id=HEALTH,
    summary="Process health check",
    responses=success_response(model=HealthResponse, description="Process is running."),
)
def health(
    settings: Annotated[AppSettings, Depends(get_settings)],
) -> HealthResponse:
    """Report whether the web process is running.

    This endpoint must not access the database.
    """

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    operation_id=READINESS,
    summary="Infrastructure readiness check",
    responses={
        **success_response(model=ReadyResponse, description="Infrastructure is ready."),
        **READINESS_ERROR_RESPONSES,
    },
)
def ready(
    readiness_check: Annotated[ReadinessCheck, Depends(get_readiness_check)],
) -> ReadyResponse:
    """Report whether required infrastructure is reachable.

    Performs a minimal ``SELECT 1`` against PostgreSQL for production wiring.
    Does not run migrations, create tables, or modify data.
    """

    try:
        readiness_check()
    except Exception as exc:
        raise ServiceNotReadyError from exc

    return ReadyResponse(status="ready")
