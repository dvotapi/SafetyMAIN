from __future__ import annotations

from fastapi import status

from backend.api.middleware import REQUEST_ID_HEADER
from backend.api.schemas.errors import APIErrorResponse

REQUEST_ID_HEADER_OPENAPI = {
    "description": "Request correlation identifier echoed on every response.",
    "schema": {"type": "string"},
}

LOCATION_HEADER_OPENAPI = {
    "description": "Relative URI of the created resource.",
    "schema": {"type": "string"},
}

COMMON_ERROR_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {"model": APIErrorResponse},
    status.HTTP_409_CONFLICT: {"model": APIErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": APIErrorResponse},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": APIErrorResponse},
}

COMMON_ERROR_RESPONSES_WITHOUT_404 = {
    status.HTTP_409_CONFLICT: {"model": APIErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": APIErrorResponse},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": APIErrorResponse},
}

SEARCH_ERROR_RESPONSES = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": APIErrorResponse},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": APIErrorResponse},
}

READINESS_ERROR_RESPONSES = {
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": APIErrorResponse},
    status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": APIErrorResponse},
}


def created_response(*, model: type[object], description: str) -> dict[int | str, dict[str, object]]:
    return {
        status.HTTP_201_CREATED: {
            "model": model,
            "description": description,
            "headers": {
                "Location": LOCATION_HEADER_OPENAPI,
                REQUEST_ID_HEADER: REQUEST_ID_HEADER_OPENAPI,
            },
        }
    }


def success_response(*, model: type[object], description: str) -> dict[int | str, dict[str, object]]:
    return {
        status.HTTP_200_OK: {
            "model": model,
            "description": description,
            "headers": {
                REQUEST_ID_HEADER: REQUEST_ID_HEADER_OPENAPI,
            },
        }
    }


def no_content_response(*, description: str) -> dict[int | str, dict[str, object]]:
    return {
        status.HTTP_204_NO_CONTENT: {
            "description": description,
            "headers": {
                REQUEST_ID_HEADER: REQUEST_ID_HEADER_OPENAPI,
            },
        }
    }
