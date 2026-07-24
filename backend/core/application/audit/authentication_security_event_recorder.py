from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID, uuid4

from backend.core.application.audit.authentication_failure_codes import (
    AUTHENTICATION_LOGIN_FAILURE_CODES,
    AUTHENTICATION_REFRESH_FAILURE_CODES,
)
from backend.core.contracts.clock import ClockContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.entities.audit_event import AuditEvent
from backend.core.domain.security_events import security_event_descriptor_for
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_event_id import AuditEventId
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType

logger = logging.getLogger(__name__)

UowFactory = Callable[[], UnitOfWorkContract]

MAX_REQUEST_ID_LENGTH = 128
MAX_CLIENT_IP_LENGTH = 64
MAX_USER_AGENT_LENGTH = 512
PASSWORD_AUTHENTICATION_METHOD = "password"

_SENSITIVE_METADATA_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "access_token",
        "refresh_token",
        "authorization",
        "authorization_header",
        "token",
        "jwt",
        "secret",
        "jti",
        "token_id_hash",
        "current_token_id_hash",
        "previous_token_id_hash",
    }
)


@dataclass(frozen=True, slots=True)
class AuthenticationAuditContext:
    """Transport-neutral safe metadata for authentication security events."""

    request_id: str | None = None
    actor_user_id: UserId | None = None
    organization_id: OrganizationId | None = None
    client_ip: str | None = None
    user_agent: str | None = None

    def with_actor(self, user_id: UserId) -> AuthenticationAuditContext:
        return replace(self, actor_user_id=user_id)

    def normalized(self) -> AuthenticationAuditContext:
        return AuthenticationAuditContext(
            request_id=_normalize_optional_string(
                self.request_id,
                max_length=MAX_REQUEST_ID_LENGTH,
            ),
            actor_user_id=self.actor_user_id,
            organization_id=self.organization_id,
            client_ip=_normalize_optional_string(
                self.client_ip,
                max_length=MAX_CLIENT_IP_LENGTH,
            ),
            user_agent=_normalize_optional_string(
                self.user_agent,
                max_length=MAX_USER_AGENT_LENGTH,
            ),
        )


class AuthenticationSecurityEventRecorder:
    """Records taxonomy-backed authentication security events observationally."""

    def __init__(
        self,
        clock: ClockContract,
        uow_factory: UowFactory,
    ) -> None:
        self._clock = clock
        self._uow_factory = uow_factory

    def record_login_succeeded(
        self,
        context: AuthenticationAuditContext,
        *,
        user_id: UserId,
        authentication_method: str = PASSWORD_AUTHENTICATION_METHOD,
    ) -> None:
        actor_context = context.with_actor(user_id)
        self._record(
            AuditAction.AUTHENTICATION_LOGIN_SUCCEEDED,
            actor_context,
            outcome=AuditOutcome.SUCCESS,
            resource_id=user_id.value,
            metadata={"authentication_method": authentication_method},
        )

    def record_login_failed(
        self,
        context: AuthenticationAuditContext,
        *,
        failure_reason: str,
        user_id: UserId | None = None,
    ) -> None:
        if failure_reason not in AUTHENTICATION_LOGIN_FAILURE_CODES:
            raise ValueError(f"Unsupported login failure reason: {failure_reason!r}.")
        actor_context = context.with_actor(user_id) if user_id is not None else context
        self._record(
            AuditAction.AUTHENTICATION_LOGIN_FAILED,
            actor_context,
            outcome=AuditOutcome.FAILURE,
            resource_id=user_id.value if user_id is not None else None,
            failure_code=failure_reason,
        )

    def record_refresh_succeeded(
        self,
        context: AuthenticationAuditContext,
        *,
        user_id: UserId,
        session_id: object | None = None,
    ) -> None:
        actor_context = context.with_actor(user_id)
        metadata: dict[str, object] = {}
        if session_id is not None and hasattr(session_id, "value"):
            metadata["session_id"] = str(session_id.value)
        self._record(
            AuditAction.AUTHENTICATION_REFRESH_SUCCEEDED,
            actor_context,
            outcome=AuditOutcome.SUCCESS,
            resource_id=user_id.value,
            metadata=metadata or None,
        )

    def record_refresh_failed(
        self,
        context: AuthenticationAuditContext,
        *,
        failure_reason: str,
    ) -> None:
        if failure_reason not in AUTHENTICATION_REFRESH_FAILURE_CODES:
            raise ValueError(f"Unsupported refresh failure reason: {failure_reason!r}.")
        # Refresh failures must not treat untrusted JWT subjects as actors.
        actorless_context = replace(context, actor_user_id=None)
        self._record(
            AuditAction.AUTHENTICATION_REFRESH_FAILED,
            actorless_context,
            outcome=AuditOutcome.FAILURE,
            resource_id=None,
            failure_code=failure_reason,
        )

    def record_refresh_reuse_detected(
        self,
        context: AuthenticationAuditContext,
        *,
        user_id: UserId,
        session_id: object,
    ) -> None:
        actor_context = context.with_actor(user_id)
        metadata: dict[str, object] = {
            "revocation_reason": "token_reuse_detected",
        }
        if hasattr(session_id, "value"):
            metadata["session_id"] = str(session_id.value)
        self._record(
            AuditAction.AUTHENTICATION_REFRESH_REUSE_DETECTED,
            actor_context,
            outcome=AuditOutcome.FAILURE,
            resource_id=user_id.value,
            failure_code="refresh_token_reuse_detected",
            metadata=metadata,
        )

    def record_logout_succeeded(
        self,
        context: AuthenticationAuditContext,
        *,
        user_id: UserId | None = None,
        session_id: object | None = None,
        revocation_reason: str | None = None,
    ) -> None:
        actor_context = context.with_actor(user_id) if user_id is not None else context
        metadata: dict[str, object] = {}
        if session_id is not None and hasattr(session_id, "value"):
            metadata["session_id"] = str(session_id.value)
        if revocation_reason is not None:
            metadata["revocation_reason"] = revocation_reason
        self._record(
            AuditAction.AUTHENTICATION_LOGOUT_SUCCEEDED,
            actor_context,
            outcome=AuditOutcome.SUCCESS,
            resource_id=user_id.value if user_id is not None else None,
            metadata=metadata or None,
        )

    def record_session_revoked(
        self,
        context: AuthenticationAuditContext,
        *,
        user_id: UserId,
        revocation_reason: str,
        revoked_session_count: int,
    ) -> None:
        actor_context = context.with_actor(user_id)
        self._record(
            AuditAction.AUTHENTICATION_SESSION_REVOKED,
            actor_context,
            outcome=AuditOutcome.SUCCESS,
            resource_id=user_id.value,
            metadata={
                "revocation_reason": revocation_reason,
                "revoked_session_count": revoked_session_count,
            },
        )

    def _record(
        self,
        action: AuditAction,
        context: AuthenticationAuditContext,
        *,
        outcome: AuditOutcome,
        resource_id: UUID | None,
        failure_code: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        descriptor = security_event_descriptor_for(action.value)
        if descriptor is None:
            raise ValueError(f"Unregistered authentication security event: {action.value!r}.")
        if outcome not in descriptor.allowed_outcomes:
            raise ValueError(
                f"Outcome {outcome.value!r} is not allowed for event {action.value!r}."
            )

        safe_context = context.normalized()
        event_metadata = self._build_metadata(safe_context, metadata)
        event = AuditEvent(
            id=AuditEventId(value=uuid4()),
            actor_user_id=safe_context.actor_user_id,
            authorization_organization_id=safe_context.organization_id,
            target_organization_id=None,
            action=action,
            resource_type=AuditResourceType.SESSION,
            resource_id=resource_id,
            outcome=outcome,
            failure_code=failure_code if outcome is AuditOutcome.FAILURE else None,
            metadata=event_metadata,
            occurred_at=self._clock.now(),
        )

        try:
            with self._uow_factory() as unit_of_work:
                unit_of_work.audit_events.add(event)
                unit_of_work.commit()
        except Exception:
            logger.exception(
                "Failed to persist authentication security event.",
                extra={
                    "audit_action": action.value,
                    "audit_outcome": outcome.value,
                    "audit_failure_code": failure_code,
                    "request_id": safe_context.request_id,
                    "actor_user_id": (
                        str(safe_context.actor_user_id.value)
                        if safe_context.actor_user_id
                        else None
                    ),
                    "organization_id": (
                        str(safe_context.organization_id.value)
                        if safe_context.organization_id
                        else None
                    ),
                },
            )

    def _build_metadata(
        self,
        context: AuthenticationAuditContext,
        metadata: Mapping[str, object] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if context.request_id is not None:
            payload["request_id"] = context.request_id
        if context.client_ip is not None:
            payload["client_ip"] = context.client_ip
        if context.user_agent is not None:
            payload["user_agent"] = context.user_agent

        if metadata:
            sensitive = _SENSITIVE_METADATA_KEYS.intersection(metadata)
            if sensitive:
                raise ValueError(
                    f"Sensitive authentication metadata keys are prohibited: "
                    f"{sorted(sensitive)}."
                )
            payload.update(dict(metadata))

        return payload


def _normalize_optional_string(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        return normalized[:max_length]
    return normalized
