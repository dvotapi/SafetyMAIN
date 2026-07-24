from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.core.application.audit.authentication_failure_codes import (
    AUTHENTICATION_FORBIDDEN,
    EXPIRED_REFRESH_TOKEN,
    INVALID_CREDENTIALS,
    INVALID_REFRESH_TOKEN,
    INVALID_TOKEN_TYPE,
)
from backend.core.application.audit.authentication_security_event_recorder import (
    AuthenticationAuditContext,
    AuthenticationSecurityEventRecorder,
)
from backend.core.domain.security_events import (
    SecurityEventSignificance,
    security_event_descriptor_for,
)
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType
from backend.core.infrastructure.persistence.in_memory import (
    InMemoryAuditEventRepository,
    InMemoryUnitOfWork,
)


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


class FailingAuditUnitOfWork(InMemoryUnitOfWork):
    def commit(self) -> None:
        raise RuntimeError("audit persistence failed")


@pytest.fixture
def recorder_stack():
    audit_events = InMemoryAuditEventRepository()
    clock = FixedClock(datetime(2026, 7, 24, 12, 0, tzinfo=UTC))

    def uow_factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(audit_events=audit_events)

    recorder = AuthenticationSecurityEventRecorder(clock, uow_factory)
    return recorder, audit_events


def _context(**overrides: object) -> AuthenticationAuditContext:
    defaults = {
        "request_id": "req-123",
        "client_ip": "198.51.100.10",
        "user_agent": "pytest-agent",
    }
    defaults.update(overrides)
    return AuthenticationAuditContext(**defaults)  # type: ignore[arg-type]


def test_record_login_succeeded_uses_taxonomy_and_safe_metadata(recorder_stack) -> None:
    recorder, audit_events = recorder_stack
    user_id = UserId(value=uuid4())

    recorder.record_login_succeeded(_context(), user_id=user_id)

    event = next(iter(audit_events.snapshot().values()))
    descriptor = security_event_descriptor_for(event.action.value)
    assert descriptor is not None
    assert event.action is AuditAction.AUTHENTICATION_LOGIN_SUCCEEDED
    assert event.action.value == "authentication.login.succeeded"
    assert event.outcome is AuditOutcome.SUCCESS
    assert event.actor_user_id == user_id
    assert event.resource_type is AuditResourceType.SESSION
    assert event.resource_id == user_id.value
    assert event.metadata["authentication_method"] == "password"
    assert event.metadata["request_id"] == "req-123"
    assert event.metadata["client_ip"] == "198.51.100.10"
    assert event.metadata["user_agent"] == "pytest-agent"
    assert descriptor.default_security_significance is SecurityEventSignificance.INFORMATIONAL


def test_record_login_failed_supports_unknown_actor(recorder_stack) -> None:
    recorder, audit_events = recorder_stack

    recorder.record_login_failed(
        _context(actor_user_id=None),
        failure_reason=INVALID_CREDENTIALS,
    )

    event = next(iter(audit_events.snapshot().values()))
    assert event.action is AuditAction.AUTHENTICATION_LOGIN_FAILED
    assert event.outcome is AuditOutcome.FAILURE
    assert event.failure_code == INVALID_CREDENTIALS
    assert event.actor_user_id is None
    assert event.resource_id is None


def test_record_login_failed_rejects_unsupported_reason(recorder_stack) -> None:
    recorder, _ = recorder_stack

    with pytest.raises(ValueError, match="Unsupported login failure reason"):
        recorder.record_login_failed(_context(), failure_reason="raw exception text")


def test_record_refresh_succeeded(recorder_stack) -> None:
    recorder, audit_events = recorder_stack
    user_id = UserId(value=uuid4())

    recorder.record_refresh_succeeded(_context(), user_id=user_id)

    event = next(iter(audit_events.snapshot().values()))
    assert event.action is AuditAction.AUTHENTICATION_REFRESH_SUCCEEDED
    assert event.outcome is AuditOutcome.SUCCESS
    assert event.actor_user_id == user_id


def test_record_refresh_failed_ignores_untrusted_actor(recorder_stack) -> None:
    recorder, audit_events = recorder_stack
    untrusted = UserId(value=uuid4())

    recorder.record_refresh_failed(
        _context(actor_user_id=untrusted),
        failure_reason=EXPIRED_REFRESH_TOKEN,
    )

    event = next(iter(audit_events.snapshot().values()))
    assert event.action is AuditAction.AUTHENTICATION_REFRESH_FAILED
    assert event.failure_code == EXPIRED_REFRESH_TOKEN
    assert event.actor_user_id is None


def test_record_refresh_failed_rejects_unsupported_reason(recorder_stack) -> None:
    recorder, _ = recorder_stack

    with pytest.raises(ValueError, match="Unsupported refresh failure reason"):
        recorder.record_refresh_failed(_context(), failure_reason="jwt.exceptions.DecodeError")


def test_optional_organization_is_persisted_when_provided(recorder_stack) -> None:
    recorder, audit_events = recorder_stack
    organization_id = OrganizationId(value=uuid4())
    user_id = UserId(value=uuid4())

    recorder.record_login_succeeded(
        _context(organization_id=organization_id),
        user_id=user_id,
    )

    event = next(iter(audit_events.snapshot().values()))
    assert event.authorization_organization_id == organization_id


def test_metadata_validation_rejects_sensitive_keys(recorder_stack) -> None:
    recorder, _ = recorder_stack
    user_id = UserId(value=uuid4())

    with pytest.raises(ValueError, match="Sensitive authentication metadata"):
        recorder._record(
            AuditAction.AUTHENTICATION_LOGIN_SUCCEEDED,
            _context(),
            outcome=AuditOutcome.SUCCESS,
            resource_id=user_id.value,
            metadata={"password": "secret-value"},
        )


def test_metadata_validation_rejects_unsupported_keys(recorder_stack) -> None:
    recorder, _ = recorder_stack
    user_id = UserId(value=uuid4())

    with pytest.raises(ValueError, match="Unsupported audit metadata keys"):
        recorder._record(
            AuditAction.AUTHENTICATION_LOGIN_SUCCEEDED,
            _context(),
            outcome=AuditOutcome.SUCCESS,
            resource_id=user_id.value,
            metadata={"email": "operator@example.com"},
        )


def test_context_string_normalization_trims_and_truncates(recorder_stack) -> None:
    recorder, audit_events = recorder_stack
    user_id = UserId(value=uuid4())

    recorder.record_login_succeeded(
        AuthenticationAuditContext(
            request_id="  req-trim  ",
            client_ip="  203.0.113.1  ",
            user_agent="x" * 600,
        ),
        user_id=user_id,
    )

    event = next(iter(audit_events.snapshot().values()))
    assert event.metadata["request_id"] == "req-trim"
    assert event.metadata["client_ip"] == "203.0.113.1"
    assert len(event.metadata["user_agent"]) == 512


def test_audit_persistence_failure_is_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audit_events = InMemoryAuditEventRepository()
    clock = FixedClock(datetime(2026, 7, 24, 12, 0, tzinfo=UTC))

    def failing_factory() -> InMemoryUnitOfWork:
        return FailingAuditUnitOfWork(audit_events=audit_events)

    recorder = AuthenticationSecurityEventRecorder(clock, failing_factory)
    logged: list[str] = []

    def capture_exception(message: str, *args: object, **kwargs: object) -> None:
        logged.append(message)

    monkeypatch.setattr(
        "backend.core.application.audit.authentication_security_event_recorder.logger.exception",
        capture_exception,
    )

    recorder.record_login_failed(
        _context(),
        failure_reason=AUTHENTICATION_FORBIDDEN,
        user_id=UserId(value=uuid4()),
    )
    recorder.record_refresh_failed(
        _context(),
        failure_reason=INVALID_TOKEN_TYPE,
    )

    assert logged
    assert all("Failed to persist authentication security event." in item for item in logged)
    assert audit_events.snapshot() == {}


def test_taxonomy_lookup_for_all_authentication_actions() -> None:
    expected = {
        AuditAction.AUTHENTICATION_LOGIN_SUCCEEDED: AuditOutcome.SUCCESS,
        AuditAction.AUTHENTICATION_LOGIN_FAILED: AuditOutcome.FAILURE,
        AuditAction.AUTHENTICATION_REFRESH_SUCCEEDED: AuditOutcome.SUCCESS,
        AuditAction.AUTHENTICATION_REFRESH_FAILED: AuditOutcome.FAILURE,
    }
    for action, outcome in expected.items():
        descriptor = security_event_descriptor_for(action.value)
        assert descriptor is not None
        assert descriptor.allowed_outcomes == frozenset({outcome})
        assert action.value.startswith("authentication.")


def test_supported_refresh_failure_codes_are_recorded(recorder_stack) -> None:
    recorder, audit_events = recorder_stack

    for reason in (
        INVALID_REFRESH_TOKEN,
        EXPIRED_REFRESH_TOKEN,
        INVALID_TOKEN_TYPE,
    ):
        recorder.record_refresh_failed(_context(), failure_reason=reason)

    codes = {event.failure_code for event in audit_events.snapshot().values()}
    assert codes == {
        INVALID_REFRESH_TOKEN,
        EXPIRED_REFRESH_TOKEN,
        INVALID_TOKEN_TYPE,
    }
