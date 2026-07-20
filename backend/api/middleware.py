from __future__ import annotations

import re
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_STATE_ATTR = "request_id"
MAX_REQUEST_ID_LENGTH = 128
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def normalize_request_id(raw_value: str | None) -> str:
    """Accept a safe client-provided request ID or generate a new one."""

    if raw_value is None:
        return str(uuid.uuid4())

    candidate = raw_value.strip()
    if (
        not candidate
        or len(candidate) > MAX_REQUEST_ID_LENGTH
        or _REQUEST_ID_PATTERN.fullmatch(candidate) is None
    ):
        return str(uuid.uuid4())

    return candidate


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, REQUEST_ID_STATE_ATTR, None)


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        request_id = normalize_request_id(request.headers.get(REQUEST_ID_HEADER))
        setattr(request.state, REQUEST_ID_STATE_ATTR, request_id)
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
