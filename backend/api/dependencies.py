from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Path, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
from backend.api.middleware import get_request_id
from backend.bootstrap.container import AppContainer, ReadinessCheck, UowFactory
from backend.bootstrap.settings import AppSettings
from backend.core.application.handlers.archive_knowledge_object import (
    ArchiveKnowledgeObjectHandler,
)
from backend.core.application.handlers.create_knowledge_object import (
    CreateKnowledgeObjectHandler,
)
from backend.core.application.handlers.delete_knowledge_object import (
    DeleteKnowledgeObjectHandler,
)
from backend.core.application.handlers.get_connected_knowledge_objects import (
    GetConnectedKnowledgeObjectsHandler,
)
from backend.core.application.handlers.get_incoming_relations import (
    GetIncomingRelationsHandler,
)
from backend.core.application.handlers.get_outgoing_relations import (
    GetOutgoingRelationsHandler,
)
from backend.core.application.handlers.get_knowledge_object import (
    GetKnowledgeObjectHandler,
)
from backend.core.application.handlers.get_knowledge_object_history import (
    GetKnowledgeObjectHistoryHandler,
)
from backend.core.application.handlers.create_knowledge_object_relation import (
    CreateKnowledgeObjectRelationHandler,
)
from backend.core.application.handlers.get_knowledge_object_relation import (
    GetKnowledgeObjectRelationHandler,
)
from backend.core.application.handlers.remove_knowledge_object_relation import (
    RemoveKnowledgeObjectRelationHandler,
)
from backend.core.application.handlers.search_knowledge_objects import (
    SearchKnowledgeObjectsHandler,
)
from backend.core.application.handlers.authenticate_user import AuthenticateUserHandler
from backend.core.application.handlers.refresh_authentication import (
    RefreshAuthenticationHandler,
)
from backend.core.application.handlers.restore_knowledge_object import (
    RestoreKnowledgeObjectHandler,
)
from backend.core.application.handlers.update_knowledge_object import (
    UpdateKnowledgeObjectHandler,
)
from backend.core.application.handlers.create_user import CreateUserHandler
from backend.core.application.handlers.get_user import GetUserHandler
from backend.core.application.handlers.list_users import ListUsersHandler
from backend.core.application.handlers.update_user import UpdateUserHandler
from backend.core.application.handlers.user_lifecycle import (
    ActivateUserHandler,
    DeactivateUserHandler,
)
from backend.core.application.handlers.create_organization import CreateOrganizationHandler
from backend.core.application.handlers.get_organization import GetOrganizationHandler
from backend.core.application.handlers.list_organizations import ListOrganizationsHandler
from backend.core.application.handlers.update_organization import UpdateOrganizationHandler
from backend.core.application.handlers.organization_lifecycle import (
    ActivateOrganizationHandler,
    DeactivateOrganizationHandler,
)
from backend.core.application.handlers.create_membership import CreateMembershipHandler
from backend.core.application.handlers.get_membership import GetMembershipHandler
from backend.core.application.handlers.list_memberships import ListMembershipsHandler
from backend.core.application.handlers.update_membership_role import UpdateMembershipRoleHandler
from backend.core.application.handlers.membership_lifecycle import (
    ActivateMembershipHandler,
    DeactivateMembershipHandler,
)
from backend.core.application.policies.membership_administration import (
    MembershipAuthorizationContext,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.contracts.token_service import TokenValidationError
from backend.core.application.exceptions.authentication import UnauthenticatedError
from backend.core.application.context.tenant_context import TenantContext
from backend.core.domain.value_objects import KnowledgeObjectId, MembershipId, OrganizationId, Permission, UserId
from backend.core.domain.value_objects.permission import SystemPermission
from backend.api.security import SecurityContext


def require_permission(
    permission: SystemPermission | Permission,
) -> Callable[..., TenantContext]:
    """Opt-in FastAPI dependency for role-based permission checks."""

    required_permission = (
        permission
        if isinstance(permission, Permission)
        else Permission.from_system_permission(permission)
    )

    def _dependency(
        tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
        container: Annotated[AppContainer, Depends(get_container)],
        settings: Annotated[AppSettings, Depends(get_settings)],
    ) -> TenantContext:
        if not settings.auth_enforcement:
            return tenant_context

        actor_user_id = tenant_context.actor_user_id
        if actor_user_id is None:
            raise UnauthenticatedError()

        container.authorization_service.require_permission(
            actor_user_id=actor_user_id,
            organization_id=tenant_context.organization_id,
            permission=required_permission,
        )
        return tenant_context

    return _dependency


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_settings(request: Request) -> AppSettings:
    return request.app.state.settings


def get_uow_factory(container: AppContainer = Depends(get_container)) -> UowFactory:
    return container.uow_factory


def get_readiness_check(
    container: AppContainer = Depends(get_container),
) -> ReadinessCheck:
    return container.readiness_check


def get_uow(
    uow_factory: UowFactory = Depends(get_uow_factory),
) -> Iterator[UnitOfWorkContract]:
    """Provide a request-scoped Unit of Work.

    The dependency enters and exits the UoW context manager but never commits.
    Transaction ownership remains with application use cases.
    """

    with uow_factory() as uow:
        yield uow


def _parse_optional_organization_header(
    raw_value: str | None,
) -> OrganizationId | None:
    if raw_value is None:
        return None
    try:
        return OrganizationId(value=raw_value)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def _require_organization_header(raw_value: str | None) -> OrganizationId:
    if raw_value is None:
        raise RequestValidationError(
            [
                {
                    "type": "missing",
                    "loc": ("header", ORGANIZATION_ID_HEADER),
                    "msg": "Field required",
                    "input": None,
                }
            ]
        )
    return _parse_optional_organization_header(raw_value)  # type: ignore[return-value]


def _extract_bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise UnauthenticatedError()

    return token.strip()


def get_tenant_context(
    request: Request,
    settings: Annotated[AppSettings, Depends(get_settings)],
    container: Annotated[AppContainer, Depends(get_container)],
    x_organization_id: Annotated[str | None, Header(alias=ORGANIZATION_ID_HEADER)] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> TenantContext:
    request_id = get_request_id(request)
    header_organization_id = _parse_optional_organization_header(x_organization_id)

    if not settings.auth_enforcement:
        organization_id = _require_organization_header(x_organization_id)
        return TenantContext(
            security_context=SecurityContext.anonymous(request_id=request_id),
            organization_id=organization_id,
        )

    bearer_token = _extract_bearer_token(authorization)
    if bearer_token is None:
        raise UnauthenticatedError()

    try:
        token_claims = container.token_service.validate_access_token_claims(bearer_token)
    except TokenValidationError as exc:
        raise UnauthenticatedError() from exc

    security_context = SecurityContext.authenticated(
        user_id=token_claims.user_id,
        authentication_method="bearer_jwt",
        request_id=request_id,
    )
    organization_id = container.tenant_context_resolver.resolve_organization_id(
        user_id=token_claims.user_id,
        token_organization_id=token_claims.organization_id,
        header_organization_id=header_organization_id,
    )
    tenant_context = container.tenant_context_resolver.build_tenant_context(
        security_context=security_context,
        organization_id=organization_id,
    )
    container.authorization_service.require_organization_access(
        actor_user_id=token_claims.user_id,
        organization_id=organization_id,
    )
    return tenant_context


def get_organization_id(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
) -> OrganizationId:
    return tenant_context.organization_id


def get_knowledge_object_id(
    knowledge_object_id: Annotated[UUID, Path()],
) -> KnowledgeObjectId:
    try:
        return KnowledgeObjectId(value=knowledge_object_id)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def get_user_id(
    user_id: Annotated[UUID, Path()],
) -> UserId:
    try:
        return UserId(value=user_id)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def get_target_organization_id(
    organization_id: Annotated[UUID, Path()],
) -> OrganizationId:
    try:
        return OrganizationId(value=organization_id)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def get_create_user_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> CreateUserHandler:
    return CreateUserHandler(uow)


def get_get_user_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> GetUserHandler:
    return GetUserHandler(uow)


def get_list_users_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> ListUsersHandler:
    return ListUsersHandler(uow)


def get_update_user_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> UpdateUserHandler:
    return UpdateUserHandler(uow)


def get_activate_user_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> ActivateUserHandler:
    return ActivateUserHandler(uow)


def get_deactivate_user_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> DeactivateUserHandler:
    return DeactivateUserHandler(uow)


def get_create_organization_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> CreateOrganizationHandler:
    return CreateOrganizationHandler(uow)


def get_get_organization_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> GetOrganizationHandler:
    return GetOrganizationHandler(uow)


def get_list_organizations_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> ListOrganizationsHandler:
    return ListOrganizationsHandler(uow)


def get_update_organization_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> UpdateOrganizationHandler:
    return UpdateOrganizationHandler(uow)


def get_activate_organization_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> ActivateOrganizationHandler:
    return ActivateOrganizationHandler(uow)


def get_deactivate_organization_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> DeactivateOrganizationHandler:
    return DeactivateOrganizationHandler(uow)


def get_membership_id(
    membership_id: Annotated[UUID, Path()],
) -> MembershipId:
    try:
        return MembershipId(value=membership_id)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def get_membership_authorization_context(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    uow: UnitOfWorkContract = Depends(get_uow),
) -> MembershipAuthorizationContext:
    actor_user_id = tenant_context.actor_user_id
    if actor_user_id is None:
        raise UnauthenticatedError()

    auth_membership = uow.memberships.get_by_user_and_organization(
        actor_user_id,
        tenant_context.organization_id,
    )
    if auth_membership is None:
        from backend.core.application.exceptions.authorization import MembershipRequiredError

        raise MembershipRequiredError()

    return MembershipAuthorizationContext(
        actor_user_id=actor_user_id,
        authorization_organization_id=tenant_context.organization_id,
        authorization_membership_id=auth_membership.id,
    )


def get_create_membership_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> CreateMembershipHandler:
    return CreateMembershipHandler(uow)


def get_get_membership_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> GetMembershipHandler:
    return GetMembershipHandler(uow)


def get_list_memberships_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> ListMembershipsHandler:
    return ListMembershipsHandler(uow)


def get_update_membership_role_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> UpdateMembershipRoleHandler:
    return UpdateMembershipRoleHandler(uow)


def get_activate_membership_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> ActivateMembershipHandler:
    return ActivateMembershipHandler(uow)


def get_deactivate_membership_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> DeactivateMembershipHandler:
    return DeactivateMembershipHandler(uow)


def get_create_knowledge_object_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> CreateKnowledgeObjectHandler:
    return CreateKnowledgeObjectHandler(uow)


def get_get_knowledge_object_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> GetKnowledgeObjectHandler:
    return GetKnowledgeObjectHandler(uow)


def get_get_knowledge_object_history_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> GetKnowledgeObjectHistoryHandler:
    return GetKnowledgeObjectHistoryHandler(uow)


def get_update_knowledge_object_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> UpdateKnowledgeObjectHandler:
    return UpdateKnowledgeObjectHandler(uow)


def get_archive_knowledge_object_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> ArchiveKnowledgeObjectHandler:
    return ArchiveKnowledgeObjectHandler(uow)


def get_restore_knowledge_object_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> RestoreKnowledgeObjectHandler:
    return RestoreKnowledgeObjectHandler(uow)


def get_delete_knowledge_object_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> DeleteKnowledgeObjectHandler:
    return DeleteKnowledgeObjectHandler(uow)


def get_create_knowledge_object_relation_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> CreateKnowledgeObjectRelationHandler:
    return CreateKnowledgeObjectRelationHandler(uow)


def get_get_knowledge_object_relation_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> GetKnowledgeObjectRelationHandler:
    return GetKnowledgeObjectRelationHandler(uow)


def get_remove_knowledge_object_relation_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> RemoveKnowledgeObjectRelationHandler:
    return RemoveKnowledgeObjectRelationHandler(uow)


def get_get_outgoing_relations_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> GetOutgoingRelationsHandler:
    return GetOutgoingRelationsHandler(uow)


def get_get_incoming_relations_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> GetIncomingRelationsHandler:
    return GetIncomingRelationsHandler(uow)


def get_get_connected_knowledge_objects_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> GetConnectedKnowledgeObjectsHandler:
    return GetConnectedKnowledgeObjectsHandler(uow)


def get_search_knowledge_objects_handler(
    uow: UnitOfWorkContract = Depends(get_uow),
) -> SearchKnowledgeObjectsHandler:
    return SearchKnowledgeObjectsHandler(uow)


def get_authenticate_user_handler(
    container: AppContainer = Depends(get_container),
) -> AuthenticateUserHandler:
    return AuthenticateUserHandler(
        user_lookup=container.user_lookup,
        user_credentials=container.user_credentials,
        password_hasher=container.password_hasher,
        token_service=container.token_service,
    )


def get_refresh_authentication_handler(
    container: AppContainer = Depends(get_container),
) -> RefreshAuthenticationHandler:
    return RefreshAuthenticationHandler(container.token_service)


def get_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if authorization is None:
        raise UnauthenticatedError()

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise UnauthenticatedError()

    return token.strip()


def get_authenticated_user(
    token: Annotated[str, Depends(get_bearer_token)],
    container: AppContainer = Depends(get_container),
) -> UserId:
    try:
        return container.token_service.validate_access_token(token)
    except TokenValidationError as exc:
        raise UnauthenticatedError() from exc


def get_security_context(
    request: Request,
    user_id: UserId = Depends(get_authenticated_user),
) -> SecurityContext:
    return SecurityContext.authenticated(
        user_id=user_id,
        authentication_method="bearer_jwt",
        request_id=get_request_id(request),
    )
