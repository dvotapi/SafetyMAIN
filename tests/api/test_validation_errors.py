from __future__ import annotations

from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from backend.api.app import create_app
from backend.api.error_codes import REQUEST_VALIDATION_ERROR, REQUEST_VALIDATION_MESSAGE
from backend.bootstrap.settings import AppSettings
from tests.api.contracts.assertions import assert_error_envelope, assert_request_id_header


class _EchoPayload(BaseModel):
    name: str = Field(min_length=1)


def test_validation_errors_use_common_schema(app_settings: AppSettings) -> None:
    application = create_app(settings=app_settings)

    @application.post("/_test/echo")
    def echo(payload: _EchoPayload) -> dict[str, str]:
        return {"name": payload.name}

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.post("/_test/echo", json={"name": ""})

    body = assert_error_envelope(
        response,
        status_code=422,
        code=REQUEST_VALIDATION_ERROR,
    )
    assert body["error"]["message"] == REQUEST_VALIDATION_MESSAGE
    violations = body["error"]["details"]["violations"]
    assert isinstance(violations, list)
    assert violations
    assert violations[0]["location"] == ["body", "name"]
    assert "message" in violations[0]
    assert "type" in violations[0]
    assert_request_id_header(response)
