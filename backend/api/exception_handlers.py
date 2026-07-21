from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.error_codes import (
    APPLICATION_AUTHENTICATION_EXCEPTION_ERROR_CODES,
    APPLICATION_AUTHENTICATION_EXCEPTION_HTTP_STATUS,
    APPLICATION_AUTHENTICATION_EXCEPTION_MESSAGES,
    APPLICATION_AUTHORIZATION_EXCEPTION_ERROR_CODES,
    APPLICATION_AUTHORIZATION_EXCEPTION_HTTP_STATUS,
    APPLICATION_AUTHORIZATION_EXCEPTION_MESSAGES,
    DOMAIN_EXCEPTION_ERROR_CODES,
    DOMAIN_EXCEPTION_HTTP_STATUS,
    DOMAIN_EXCEPTION_MESSAGES,
    INTERNAL_SERVER_ERROR,
    REQUEST_VALIDATION_ERROR,
    REQUEST_VALIDATION_MESSAGE,
    SERVICE_NOT_READY,
)
from backend.api.logging import get_logger
from backend.api.middleware import REQUEST_ID_HEADER, get_request_id
from backend.api.schemas.errors import (
    APIErrorDetail,
    APIErrorResponse,
    APIValidationErrorDetails,
    APIValidationViolation,
)
from backend.core.application.exceptions.authentication import AuthenticationError
from backend.core.application.exceptions.authorization import AuthorizationError
from backend.core.domain.exceptions import SafetyMainDomainError

logger = get_logger("safetymain.api.exceptions")


class ServiceNotReadyError(Exception):
    """Raised when readiness infrastructure checks fail."""


def build_error_response(
    *,
    code: str,
    message: str,
    details: Mapping[str, object] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    payload_details: dict[str, object] | None = None
    if details:
        payload_details = dict(details)
    if request_id is not None:
        if payload_details is None:
            payload_details = {"request_id": request_id}
        else:
            payload_details = {**payload_details, "request_id": request_id}

    body = APIErrorResponse(
        error=APIErrorDetail(
            code=code,
            message=message,
            details=payload_details,
        )
    )
    return body.model_dump(exclude_none=True)


def _json_error(
    *,
    status_code: int,
    code: str,
    message: str,
    request: Request,
    details: Mapping[str, object] | None = None,
) -> JSONResponse:
    request_id = get_request_id(request)
    content = build_error_response(
        code=code,
        message=message,
        details=details,
        request_id=request_id,
    )
    headers: dict[str, str] = {}
    if request_id is not None:
        headers[REQUEST_ID_HEADER] = request_id
    return JSONResponse(status_code=status_code, content=content, headers=headers)


def _resolve_domain_exception(
    exc: SafetyMainDomainError,
) -> tuple[int, str, str] | None:
    for exception_type, status_code in DOMAIN_EXCEPTION_HTTP_STATUS.items():
        if isinstance(exc, exception_type):
            return (
                status_code,
                DOMAIN_EXCEPTION_ERROR_CODES[exception_type],
                DOMAIN_EXCEPTION_MESSAGES[exception_type],
            )
    return None


def _normalize_validation_location(raw_location: object) -> tuple[str, ...]:
    if not isinstance(raw_location, tuple | list):
        return ("body",)

    normalized: list[str] = []
    for part in raw_location:
        if isinstance(part, int):
            normalized.append(str(part))
            continue
        normalized.append(str(part))
    return tuple(normalized)


def _validation_details(exc: RequestValidationError) -> dict[str, object]:
    seen_locations: set[tuple[str, ...]] = set()
    violations: list[APIValidationViolation] = []

    for error in exc.errors():
        location = _normalize_validation_location(error.get("loc", ()))
        if location in seen_locations:
            continue
        seen_locations.add(location)
        violations.append(
            APIValidationViolation(
                location=location,
                message=str(error.get("msg", "Invalid value.")),
                type=str(error.get("type", "value_error")),
            )
        )

    return APIValidationErrorDetails(violations=tuple(violations)).model_dump(mode="json")


def _resolve_authentication_exception(
    exc: AuthenticationError,
) -> tuple[int, str, str] | None:
    for exception_type, status_code in (
        APPLICATION_AUTHENTICATION_EXCEPTION_HTTP_STATUS.items()
    ):
        if isinstance(exc, exception_type):
            return (
                status_code,
                APPLICATION_AUTHENTICATION_EXCEPTION_ERROR_CODES[exception_type],
                APPLICATION_AUTHENTICATION_EXCEPTION_MESSAGES[exception_type],
            )
    return None


def _resolve_authorization_exception(
    exc: AuthorizationError,
) -> tuple[int, str, str] | None:
    for exception_type, status_code in (
        APPLICATION_AUTHORIZATION_EXCEPTION_HTTP_STATUS.items()
    ):
        if isinstance(exc, exception_type):
            return (
                status_code,
                APPLICATION_AUTHORIZATION_EXCEPTION_ERROR_CODES[exception_type],
                APPLICATION_AUTHORIZATION_EXCEPTION_MESSAGES[exception_type],
            )
    return None


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceNotReadyError)
    async def service_not_ready_handler(
        request: Request,
        _exc: ServiceNotReadyError,
    ) -> JSONResponse:
        return _json_error(
            status_code=503,
            code=SERVICE_NOT_READY,
            message="The service is not ready.",
            request=request,
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request,
        exc: AuthenticationError,
    ) -> JSONResponse:
        resolved = _resolve_authentication_exception(exc)
        if resolved is None:
            logger.exception(
                "Unhandled authentication error on %s %s",
                request.method,
                request.url.path,
            )
            return _json_error(
                status_code=500,
                code=INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred.",
                request=request,
            )

        status_code, code, message = resolved
        return _json_error(
            status_code=status_code,
            code=code,
            message=message,
            request=request,
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request,
        exc: AuthorizationError,
    ) -> JSONResponse:
        resolved = _resolve_authorization_exception(exc)
        if resolved is None:
            logger.exception(
                "Unhandled authorization error on %s %s",
                request.method,
                request.url.path,
            )
            return _json_error(
                status_code=500,
                code=INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred.",
                request=request,
            )

        status_code, code, message = resolved
        return _json_error(
            status_code=status_code,
            code=code,
            message=message,
            request=request,
        )

    @app.exception_handler(SafetyMainDomainError)
    async def domain_error_handler(
        request: Request,
        exc: SafetyMainDomainError,
    ) -> JSONResponse:
        resolved = _resolve_domain_exception(exc)
        if resolved is None:
            logger.exception(
                "Unhandled domain error on %s %s",
                request.method,
                request.url.path,
            )
            return _json_error(
                status_code=500,
                code=INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred.",
                request=request,
            )

        status_code, code, message = resolved
        return _json_error(
            status_code=status_code,
            code=code,
            message=message,
            request=request,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _json_error(
            status_code=422,
            code=REQUEST_VALIDATION_ERROR,
            message=REQUEST_VALIDATION_MESSAGE,
            request=request,
            details=_validation_details(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        if exc.status_code == 503:
            return _json_error(
                status_code=503,
                code=SERVICE_NOT_READY,
                message="The service is not ready.",
                request=request,
            )

        return _json_error(
            status_code=500,
            code=INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred.",
            request=request,
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unexpected error on %s %s: %s",
            request.method,
            request.url.path,
            type(exc).__name__,
        )
        return _json_error(
            status_code=500,
            code=INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred.",
            request=request,
        )
