from __future__ import annotations

from uuid import UUID

from fastapi import Request
from pydantic import ValidationError

from backend.core.application.audit.permission_denial_audit import (
    PermissionDenialAuditSpec,
    resource_type_for_permission,
)
from backend.core.domain.value_objects import OrganizationId, Permission, UserId

API_V1_PREFIX = "/api/v1"


def _normalize_route_template(route_template: str) -> str:
    if route_template.startswith(API_V1_PREFIX):
        return route_template
    if route_template.startswith("/"):
        return f"{API_V1_PREFIX}{route_template}"
    return f"{API_V1_PREFIX}/{route_template}"


def build_permission_denial_audit_spec(
    *,
    request: Request,
    actor_user_id: UserId,
    authorization_organization_id: OrganizationId,
    required_permission: Permission,
) -> PermissionDenialAuditSpec:
    route = request.scope.get("route")
    route_template = _normalize_route_template(
        getattr(route, "path", request.url.path) if route is not None else request.url.path
    )
    operation_id = getattr(route, "name", None)

    path_params = request.path_params or {}
    resource_id: UUID | None = None
    for key in ("user_id", "membership_id", "invitation_id", "audit_event_id"):
        raw_value = path_params.get(key)
        if raw_value is None:
            continue
        try:
            resource_id = UUID(str(raw_value))
        except ValueError:
            resource_id = None
        break

    target_organization_id: OrganizationId | None = None
    raw_organization_id = path_params.get("organization_id")
    if raw_organization_id is not None:
        try:
            target_organization_id = OrganizationId(value=UUID(str(raw_organization_id)))
        except (ValueError, ValidationError):
            target_organization_id = None

    return PermissionDenialAuditSpec(
        actor_user_id=actor_user_id,
        authorization_organization_id=authorization_organization_id,
        required_permission=required_permission,
        resource_type=resource_type_for_permission(required_permission),
        http_method=request.method.upper(),
        route_template=route_template,
        resource_id=resource_id,
        target_organization_id=target_organization_id,
        operation_id=operation_id,
        target_identifier_present=resource_id is not None,
    )
