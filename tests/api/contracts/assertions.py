from __future__ import annotations

from httpx import Response

from backend.api.middleware import REQUEST_ID_HEADER


def assert_error_envelope(
    response: Response,
    *,
    status_code: int,
    code: str,
) -> dict[str, object]:
    assert response.status_code == status_code
    body = response.json()
    assert "error" in body
    error = body["error"]
    assert error["code"] == code
    assert isinstance(error["message"], str)
    assert error["message"]
    assert "details" in error
    assert error["details"] is not None
    assert "request_id" in error["details"]
    assert error["details"]["request_id"]
    return body


def assert_request_id_header(response: Response) -> str:
    assert REQUEST_ID_HEADER in response.headers
    request_id = response.headers[REQUEST_ID_HEADER]
    assert request_id
    return request_id


def assert_no_content_response(response: Response) -> None:
    assert response.status_code == 204
    assert response.content == b""
    assert_request_id_header(response)


def assert_location_header(response: Response, *, expected_location: str) -> None:
    assert response.status_code == 201
    assert response.headers["Location"] == expected_location
    assert_request_id_header(response)
