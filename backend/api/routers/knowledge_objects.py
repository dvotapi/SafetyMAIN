from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.security import TenantContext
from backend.api.dependencies import (
    get_archive_knowledge_object_handler,
    get_create_knowledge_object_handler,
    get_delete_knowledge_object_handler,
    get_get_connected_knowledge_objects_handler,
    get_get_incoming_relations_handler,
    get_get_knowledge_object_handler,
    get_get_knowledge_object_history_handler,
    get_get_outgoing_relations_handler,
    get_knowledge_object_id,
    get_restore_knowledge_object_handler,
    get_search_knowledge_objects_handler,
    get_update_knowledge_object_handler,
    require_permission,
)
from backend.api.params.knowledge_object_search import (
    KnowledgeObjectSearchParams,
    parse_knowledge_object_search_params,
)
from backend.api.relation_params import (
    connected_direction_query,
    optional_relation_type_query,
)
from backend.api.mappers.knowledge_objects import (
    to_knowledge_object_response,
    to_knowledge_object_responses,
)
from backend.api.openapi import (
    PROTECTED_BUSINESS_ERROR_RESPONSES,
    PROTECTED_BUSINESS_SEARCH_ERROR_RESPONSES,
    created_response,
    no_content_response,
    success_response,
)
from backend.api.operation_ids import (
    ARCHIVE_KNOWLEDGE_OBJECT,
    CREATE_KNOWLEDGE_OBJECT,
    DELETE_KNOWLEDGE_OBJECT,
    GET_CONNECTED_KNOWLEDGE_OBJECTS,
    GET_INCOMING_RELATIONS,
    GET_KNOWLEDGE_OBJECT,
    GET_KNOWLEDGE_OBJECT_HISTORY,
    GET_OUTGOING_RELATIONS,
    RESTORE_KNOWLEDGE_OBJECT,
    SEARCH_KNOWLEDGE_OBJECTS,
    UPDATE_KNOWLEDGE_OBJECT,
)
from backend.api.mappers.relations import to_relation_responses
from backend.api.schemas.knowledge_objects import (
    CreateKnowledgeObjectRequest,
    KnowledgeObjectHistoryResponse,
    KnowledgeObjectListResponse,
    KnowledgeObjectResponse,
    KnowledgeObjectSearchResponse,
    PaginationResponse,
    UpdateKnowledgeObjectRequest,
)
from backend.api.schemas.relations import KnowledgeObjectRelationListResponse
from backend.core.application.commands.archive_knowledge_object import (
    ArchiveKnowledgeObjectCommand,
)
from backend.core.application.commands.create_knowledge_object import (
    CreateKnowledgeObjectCommand,
)
from backend.core.application.commands.delete_knowledge_object import (
    DeleteKnowledgeObjectCommand,
)
from backend.core.application.commands.restore_knowledge_object import (
    RestoreKnowledgeObjectCommand,
)
from backend.core.application.commands.update_knowledge_object import (
    UpdateKnowledgeObjectCommand,
)
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
from backend.core.application.handlers.restore_knowledge_object import (
    RestoreKnowledgeObjectHandler,
)
from backend.core.application.handlers.search_knowledge_objects import (
    SearchKnowledgeObjectsHandler,
)
from backend.core.application.handlers.update_knowledge_object import (
    UpdateKnowledgeObjectHandler,
)
from backend.core.application.queries.get_connected_knowledge_objects import (
    GetConnectedKnowledgeObjectsQuery,
)
from backend.core.application.queries.get_incoming_relations import (
    GetIncomingRelationsQuery,
)
from backend.core.application.queries.get_outgoing_relations import (
    GetOutgoingRelationsQuery,
)
from backend.core.application.queries.get_knowledge_object import GetKnowledgeObjectQuery
from backend.core.application.queries.get_knowledge_object_history import (
    GetKnowledgeObjectHistoryQuery,
)
from backend.core.application.queries.search_knowledge_objects import (
    SearchKnowledgeObjectsQuery,
)
from backend.core.application.queries.relation_direction import RelationDirection
from backend.core.application.authorization.policies.resource_permissions import (
    KNOWLEDGE_OBJECT_DELETE,
    KNOWLEDGE_OBJECT_READ,
    KNOWLEDGE_OBJECT_WRITE,
    RELATION_READ,
)

from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    KnowledgeObjectVersion,
)

router = APIRouter(prefix="/knowledge-objects", tags=["Knowledge Objects"])


@router.post(
    "",
    response_model=KnowledgeObjectResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_KNOWLEDGE_OBJECT,
    summary="Create a Knowledge Object",
    responses={
        **created_response(
            model=KnowledgeObjectResponse,
            description="Knowledge Object created.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def create_knowledge_object(
    request_body: CreateKnowledgeObjectRequest,
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(KNOWLEDGE_OBJECT_WRITE)),
    ],
    handler: Annotated[
        CreateKnowledgeObjectHandler,
        Depends(get_create_knowledge_object_handler),
    ],
) -> JSONResponse:
    knowledge_object = handler.handle(
        CreateKnowledgeObjectCommand(
            object_type=request_body.type,
            organization_id=tenant_context.organization_id.value,
            payload=dict(request_body.metadata),
        )
    )
    response_body = to_knowledge_object_response(knowledge_object)
    location = f"{API_V1_PREFIX}/knowledge-objects/{knowledge_object.header.id.value}"
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response_body.model_dump(mode="json"),
        headers={"Location": location},
    )


@router.get(
    "",
    response_model=KnowledgeObjectSearchResponse,
    operation_id=SEARCH_KNOWLEDGE_OBJECTS,
    summary="Search Knowledge Objects",
    responses={
        **success_response(
            model=KnowledgeObjectSearchResponse,
            description="Search results returned.",
        ),
        **PROTECTED_BUSINESS_SEARCH_ERROR_RESPONSES,
    },
)
def search_knowledge_objects(
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(KNOWLEDGE_OBJECT_READ)),
    ],
    search_params: Annotated[
        KnowledgeObjectSearchParams,
        Depends(parse_knowledge_object_search_params),
    ],
    handler: Annotated[
        SearchKnowledgeObjectsHandler,
        Depends(get_search_knowledge_objects_handler),
    ],
) -> KnowledgeObjectSearchResponse:
    result = handler.handle(
        SearchKnowledgeObjectsQuery(
            organization_id=tenant_context.organization_id,
            object_type=search_params.object_type,
            status=search_params.status,
            metadata_equals=search_params.metadata_equals,
            include_deleted=search_params.include_deleted,
            offset=search_params.offset,
            limit=search_params.limit,
        )
    )
    return KnowledgeObjectSearchResponse(
        items=to_knowledge_object_responses(tuple(result.items)),
        pagination=PaginationResponse(
            offset=result.offset,
            limit=result.limit,
            total=result.total,
        ),
    )


@router.get(
    "/{knowledge_object_id}",
    response_model=KnowledgeObjectResponse,
    operation_id=GET_KNOWLEDGE_OBJECT,
    summary="Get a Knowledge Object",
    responses={
        **success_response(
            model=KnowledgeObjectResponse,
            description="Knowledge Object returned.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_knowledge_object(
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(KNOWLEDGE_OBJECT_READ)),
    ],
    knowledge_object_id: Annotated[KnowledgeObjectId, Depends(get_knowledge_object_id)],
    handler: Annotated[
        GetKnowledgeObjectHandler,
        Depends(get_get_knowledge_object_handler),
    ],
) -> KnowledgeObjectResponse:
    knowledge_object = handler.handle(
        GetKnowledgeObjectQuery(
            organization_id=tenant_context.organization_id,
            object_id=knowledge_object_id,
        )
    )
    return to_knowledge_object_response(knowledge_object)


@router.put(
    "/{knowledge_object_id}",
    response_model=KnowledgeObjectResponse,
    operation_id=UPDATE_KNOWLEDGE_OBJECT,
    summary="Update a Knowledge Object",
    responses={
        **success_response(
            model=KnowledgeObjectResponse,
            description="Knowledge Object updated.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def update_knowledge_object(
    request_body: UpdateKnowledgeObjectRequest,
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(KNOWLEDGE_OBJECT_WRITE)),
    ],
    knowledge_object_id: Annotated[KnowledgeObjectId, Depends(get_knowledge_object_id)],
    handler: Annotated[
        UpdateKnowledgeObjectHandler,
        Depends(get_update_knowledge_object_handler),
    ],
) -> KnowledgeObjectResponse:
    knowledge_object = handler.handle(
        UpdateKnowledgeObjectCommand(
            object_id=knowledge_object_id,
            organization_id=tenant_context.organization_id,
            expected_version=KnowledgeObjectVersion(value=request_body.version),
            payload=dict(request_body.metadata),
        )
    )
    return to_knowledge_object_response(knowledge_object)


@router.post(
    "/{knowledge_object_id}/archive",
    response_model=KnowledgeObjectResponse,
    operation_id=ARCHIVE_KNOWLEDGE_OBJECT,
    summary="Archive a Knowledge Object",
    responses={
        **success_response(
            model=KnowledgeObjectResponse,
            description="Knowledge Object archived.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def archive_knowledge_object(
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(KNOWLEDGE_OBJECT_WRITE)),
    ],
    knowledge_object_id: Annotated[KnowledgeObjectId, Depends(get_knowledge_object_id)],
    handler: Annotated[
        ArchiveKnowledgeObjectHandler,
        Depends(get_archive_knowledge_object_handler),
    ],
) -> KnowledgeObjectResponse:
    knowledge_object = handler.handle(
        ArchiveKnowledgeObjectCommand(
            object_id=knowledge_object_id,
            organization_id=tenant_context.organization_id,
        )
    )
    return to_knowledge_object_response(knowledge_object)


@router.post(
    "/{knowledge_object_id}/restore",
    response_model=KnowledgeObjectResponse,
    operation_id=RESTORE_KNOWLEDGE_OBJECT,
    summary="Restore a Knowledge Object",
    responses={
        **success_response(
            model=KnowledgeObjectResponse,
            description="Knowledge Object restored.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def restore_knowledge_object(
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(KNOWLEDGE_OBJECT_WRITE)),
    ],
    knowledge_object_id: Annotated[KnowledgeObjectId, Depends(get_knowledge_object_id)],
    handler: Annotated[
        RestoreKnowledgeObjectHandler,
        Depends(get_restore_knowledge_object_handler),
    ],
) -> KnowledgeObjectResponse:
    knowledge_object = handler.handle(
        RestoreKnowledgeObjectCommand(
            object_id=knowledge_object_id,
            organization_id=tenant_context.organization_id,
        )
    )
    return to_knowledge_object_response(knowledge_object)


@router.delete(
    "/{knowledge_object_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id=DELETE_KNOWLEDGE_OBJECT,
    summary="Soft-delete a Knowledge Object",
    responses={
        **no_content_response(description="Knowledge Object deleted."),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def delete_knowledge_object(
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(KNOWLEDGE_OBJECT_DELETE)),
    ],
    knowledge_object_id: Annotated[KnowledgeObjectId, Depends(get_knowledge_object_id)],
    handler: Annotated[
        DeleteKnowledgeObjectHandler,
        Depends(get_delete_knowledge_object_handler),
    ],
) -> Response:
    handler.handle(
        DeleteKnowledgeObjectCommand(
            object_id=knowledge_object_id,
            organization_id=tenant_context.organization_id,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{knowledge_object_id}/history",
    response_model=KnowledgeObjectHistoryResponse,
    operation_id=GET_KNOWLEDGE_OBJECT_HISTORY,
    summary="Get Knowledge Object version history",
    responses={
        **success_response(
            model=KnowledgeObjectHistoryResponse,
            description="Historical versions returned.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def get_knowledge_object_history(
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(KNOWLEDGE_OBJECT_READ)),
    ],
    knowledge_object_id: Annotated[KnowledgeObjectId, Depends(get_knowledge_object_id)],
    handler: Annotated[
        GetKnowledgeObjectHistoryHandler,
        Depends(get_get_knowledge_object_history_handler),
    ],
) -> KnowledgeObjectHistoryResponse:
    history = handler.handle(
        GetKnowledgeObjectHistoryQuery(
            organization_id=tenant_context.organization_id,
            object_id=knowledge_object_id,
        )
    )
    return KnowledgeObjectHistoryResponse(
        items=to_knowledge_object_responses(tuple(history))
    )


@router.get(
    "/{knowledge_object_id}/relations/outgoing",
    response_model=KnowledgeObjectRelationListResponse,
    operation_id=GET_OUTGOING_RELATIONS,
    summary="List outgoing relations",
    responses={
        **success_response(
            model=KnowledgeObjectRelationListResponse,
            description="Outgoing relations returned.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_outgoing_relations(
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(RELATION_READ)),
    ],
    knowledge_object_id: Annotated[KnowledgeObjectId, Depends(get_knowledge_object_id)],
    relation_type: Annotated[
        KnowledgeObjectRelationType | None,
        Depends(optional_relation_type_query),
    ],
    handler: Annotated[
        GetOutgoingRelationsHandler,
        Depends(get_get_outgoing_relations_handler),
    ],
) -> KnowledgeObjectRelationListResponse:
    relations = handler.handle(
        GetOutgoingRelationsQuery(
            organization_id=tenant_context.organization_id,
            knowledge_object_id=knowledge_object_id,
            relation_type=relation_type,
        )
    )
    return KnowledgeObjectRelationListResponse(items=to_relation_responses(tuple(relations)))


@router.get(
    "/{knowledge_object_id}/relations/incoming",
    response_model=KnowledgeObjectRelationListResponse,
    operation_id=GET_INCOMING_RELATIONS,
    summary="List incoming relations",
    responses={
        **success_response(
            model=KnowledgeObjectRelationListResponse,
            description="Incoming relations returned.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_incoming_relations(
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(RELATION_READ)),
    ],
    knowledge_object_id: Annotated[KnowledgeObjectId, Depends(get_knowledge_object_id)],
    relation_type: Annotated[
        KnowledgeObjectRelationType | None,
        Depends(optional_relation_type_query),
    ],
    handler: Annotated[
        GetIncomingRelationsHandler,
        Depends(get_get_incoming_relations_handler),
    ],
) -> KnowledgeObjectRelationListResponse:
    relations = handler.handle(
        GetIncomingRelationsQuery(
            organization_id=tenant_context.organization_id,
            knowledge_object_id=knowledge_object_id,
            relation_type=relation_type,
        )
    )
    return KnowledgeObjectRelationListResponse(items=to_relation_responses(tuple(relations)))


@router.get(
    "/{knowledge_object_id}/connected",
    response_model=KnowledgeObjectListResponse,
    operation_id=GET_CONNECTED_KNOWLEDGE_OBJECTS,
    summary="List connected Knowledge Objects",
    responses={
        **success_response(
            model=KnowledgeObjectListResponse,
            description="Connected Knowledge Objects returned.",
        ),
        **PROTECTED_BUSINESS_ERROR_RESPONSES,
    },
)
def list_connected_knowledge_objects(
    tenant_context: Annotated[
        TenantContext,
        Depends(require_permission(RELATION_READ)),
    ],
    knowledge_object_id: Annotated[KnowledgeObjectId, Depends(get_knowledge_object_id)],
    direction: Annotated[RelationDirection, Depends(connected_direction_query)],
    relation_type: Annotated[
        KnowledgeObjectRelationType | None,
        Depends(optional_relation_type_query),
    ],
    handler: Annotated[
        GetConnectedKnowledgeObjectsHandler,
        Depends(get_get_connected_knowledge_objects_handler),
    ],
) -> KnowledgeObjectListResponse:
    relations_query = GetConnectedKnowledgeObjectsQuery(
        organization_id=tenant_context.organization_id,
        knowledge_object_id=knowledge_object_id,
        direction=direction,
        relation_type=relation_type,
    )
    connected_objects = handler.handle(relations_query)
    return KnowledgeObjectListResponse(
        items=to_knowledge_object_responses(tuple(connected_objects))
    )
