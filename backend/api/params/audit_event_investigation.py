from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Query
from fastapi.exceptions import RequestValidationError

from backend.core.application.audit.authentication_security_event_recorder import (
    MAX_REQUEST_ID_LENGTH,
)
from backend.core.domain.security_events.categories import SecurityEventCategory
from backend.core.domain.security_events.query_resolution import (
    UnknownSecurityEventNameError,
    resolve_security_event_name,
)
from backend.core.domain.security_events.significance import SecurityEventSignificance
from backend.core.domain.value_objects import OrganizationId, UserId
from backend.core.domain.value_objects.audit_action import AuditAction
from backend.core.domain.value_objects.audit_outcome import AuditOutcome
from backend.core.domain.value_objects.audit_resource_type import AuditResourceType


@dataclass(frozen=True, slots=True)
class AuditEventInvestigationParams:
    offset: int
    limit: int
    event_name: AuditAction | None
    event_category: SecurityEventCategory | None
    severity: SecurityEventSignificance | None
    action: AuditAction | None
    resource_type: AuditResourceType | None
    resource_id: UUID | None
    actor_user_id: UserId | None
    outcome: AuditOutcome | None
    target_organization_id: OrganizationId | None
    request_id: str | None
    occurred_from: datetime | None
    occurred_to: datetime | None
    sort_ascending: bool


def _validation_error(message: str, *, loc: tuple[str, ...]) -> RequestValidationError:
    return RequestValidationError(
        [
            {
                "loc": loc,
                "msg": message,
                "type": "value_error",
            }
        ]
    )


def _parse_request_id(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    if not normalized:
        raise _validation_error(
            "request_id must not be empty.",
            loc=("query", "request_id"),
        )
    if len(normalized) > MAX_REQUEST_ID_LENGTH:
        raise _validation_error(
            f"request_id must be at most {MAX_REQUEST_ID_LENGTH} characters.",
            loc=("query", "request_id"),
        )
    return normalized


def _require_aware(value: datetime | None, *, field_name: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise _validation_error(
            f"{field_name} must be timezone-aware.",
            loc=("query", field_name),
        )
    return value


def get_audit_event_investigation_params(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    event_name: Annotated[
        str | None,
        Query(
            description=(
                "Canonical taxonomy event name "
                "(exact match; unknown names are rejected)."
            ),
        ),
    ] = None,
    event_category: Annotated[
        SecurityEventCategory | None,
        Query(description="Taxonomy category filter (exact match)."),
    ] = None,
    severity: Annotated[
        SecurityEventSignificance | None,
        Query(
            description=(
                "Taxonomy default security significance filter "
                "(registry metadata; exact match)."
            ),
        ),
    ] = None,
    action: Annotated[AuditAction | None, Query()] = None,
    resource_type: Annotated[AuditResourceType | None, Query()] = None,
    resource_id: Annotated[UUID | None, Query()] = None,
    actor_user_id: Annotated[UUID | None, Query()] = None,
    outcome: Annotated[AuditOutcome | None, Query()] = None,
    target_organization_id: Annotated[UUID | None, Query()] = None,
    request_id: Annotated[
        str | None,
        Query(description="Exact request correlation ID from event metadata."),
    ] = None,
    occurred_from: Annotated[
        datetime | None,
        Query(description="Inclusive lower bound for occurred_at (timezone-aware)."),
    ] = None,
    occurred_to: Annotated[
        datetime | None,
        Query(description="Exclusive upper bound for occurred_at (timezone-aware)."),
    ] = None,
    sort_ascending: Annotated[bool, Query()] = False,
) -> AuditEventInvestigationParams:
    resolved_event_name: AuditAction | None = None
    if event_name is not None:
        try:
            resolved_event_name = resolve_security_event_name(event_name)
        except UnknownSecurityEventNameError as exc:
            raise _validation_error(str(exc), loc=("query", "event_name")) from exc

    parsed_from = _require_aware(occurred_from, field_name="occurred_from")
    parsed_to = _require_aware(occurred_to, field_name="occurred_to")
    if parsed_from is not None and parsed_to is not None and parsed_from >= parsed_to:
        raise _validation_error(
            "occurred_from must be earlier than occurred_to.",
            loc=("query", "occurred_from"),
        )

    return AuditEventInvestigationParams(
        offset=offset,
        limit=limit,
        event_name=resolved_event_name,
        event_category=event_category,
        severity=severity,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_user_id=UserId(value=actor_user_id) if actor_user_id else None,
        outcome=outcome,
        target_organization_id=(
            OrganizationId(value=target_organization_id)
            if target_organization_id
            else None
        ),
        request_id=_parse_request_id(request_id),
        occurred_from=parsed_from,
        occurred_to=parsed_to,
        sort_ascending=sort_ascending,
    )
