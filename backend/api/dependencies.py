from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Path, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from backend.api.knowledge_object_params import ORGANIZATION_ID_HEADER
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
from backend.core.application.handlers.restore_knowledge_object import (
    RestoreKnowledgeObjectHandler,
)
from backend.core.application.handlers.update_knowledge_object import (
    UpdateKnowledgeObjectHandler,
)
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.domain.value_objects import KnowledgeObjectId, OrganizationId


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


def get_organization_id(
    x_organization_id: Annotated[str, Header(alias=ORGANIZATION_ID_HEADER)],
) -> OrganizationId:
    try:
        return OrganizationId(value=x_organization_id)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def get_knowledge_object_id(
    knowledge_object_id: Annotated[UUID, Path()],
) -> KnowledgeObjectId:
    try:
        return KnowledgeObjectId(value=knowledge_object_id)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


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
