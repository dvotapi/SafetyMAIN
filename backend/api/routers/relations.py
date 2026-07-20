from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from backend.api.constants import API_V1_PREFIX
from backend.api.dependencies import (
    get_create_knowledge_object_relation_handler,
    get_get_knowledge_object_relation_handler,
    get_organization_id,
    get_remove_knowledge_object_relation_handler,
)
from backend.api.mappers.relations import to_relation_response
from backend.api.openapi import (
    COMMON_ERROR_RESPONSES,
    created_response,
    no_content_response,
    success_response,
)
from backend.api.operation_ids import (
    CREATE_KNOWLEDGE_OBJECT_RELATION,
    DELETE_KNOWLEDGE_OBJECT_RELATION,
    GET_KNOWLEDGE_OBJECT_RELATION,
)
from backend.api.schemas.relations import (
    CreateKnowledgeObjectRelationRequest,
    KnowledgeObjectRelationResponse,
)
from backend.core.application.commands.create_knowledge_object_relation import (
    CreateKnowledgeObjectRelationCommand,
)
from backend.core.application.commands.remove_knowledge_object_relation import (
    RemoveKnowledgeObjectRelationCommand,
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
from backend.core.application.queries.get_knowledge_object_relation import (
    GetKnowledgeObjectRelationQuery,
)
from backend.core.domain.value_objects import (
    KnowledgeObjectId,
    KnowledgeObjectRelationType,
    OrganizationId,
)

router = APIRouter(prefix="/relations", tags=["Relations"])


def get_relation_id(relation_id: UUID) -> UUID:
    return relation_id


@router.post(
    "",
    response_model=KnowledgeObjectRelationResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id=CREATE_KNOWLEDGE_OBJECT_RELATION,
    summary="Create a directed Knowledge Object relation",
    responses={
        **created_response(
            model=KnowledgeObjectRelationResponse,
            description="Relation created.",
        ),
        **COMMON_ERROR_RESPONSES,
    },
)
def create_relation(
    request_body: CreateKnowledgeObjectRelationRequest,
    organization_id: Annotated[OrganizationId, Depends(get_organization_id)],
    handler: Annotated[
        CreateKnowledgeObjectRelationHandler,
        Depends(get_create_knowledge_object_relation_handler),
    ],
) -> JSONResponse:
    relation = handler.handle(
        CreateKnowledgeObjectRelationCommand(
            organization_id=organization_id,
            source_object_id=KnowledgeObjectId(value=request_body.source_object_id),
            target_object_id=KnowledgeObjectId(value=request_body.target_object_id),
            relation_type=KnowledgeObjectRelationType(value=request_body.type),
        )
    )
    response_body = to_relation_response(relation)
    location = f"{API_V1_PREFIX}/relations/{relation.relation_id}"
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response_body.model_dump(mode="json"),
        headers={"Location": location},
    )


@router.get(
    "/{relation_id}",
    response_model=KnowledgeObjectRelationResponse,
    operation_id=GET_KNOWLEDGE_OBJECT_RELATION,
    summary="Get a Knowledge Object relation",
    responses={
        **success_response(
            model=KnowledgeObjectRelationResponse,
            description="Relation returned.",
        ),
        **COMMON_ERROR_RESPONSES,
    },
)
def get_relation(
    relation_id: Annotated[UUID, Depends(get_relation_id)],
    organization_id: Annotated[OrganizationId, Depends(get_organization_id)],
    handler: Annotated[
        GetKnowledgeObjectRelationHandler,
        Depends(get_get_knowledge_object_relation_handler),
    ],
) -> KnowledgeObjectRelationResponse:
    relation = handler.handle(
        GetKnowledgeObjectRelationQuery(
            organization_id=organization_id,
            relation_id=relation_id,
        )
    )
    return to_relation_response(relation)


@router.delete(
    "/{relation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id=DELETE_KNOWLEDGE_OBJECT_RELATION,
    summary="Delete a Knowledge Object relation",
    responses={
        **no_content_response(description="Relation deleted."),
        **COMMON_ERROR_RESPONSES,
    },
)
def delete_relation(
    relation_id: Annotated[UUID, Depends(get_relation_id)],
    organization_id: Annotated[OrganizationId, Depends(get_organization_id)],
    handler: Annotated[
        RemoveKnowledgeObjectRelationHandler,
        Depends(get_remove_knowledge_object_relation_handler),
    ],
) -> Response:
    handler.handle(
        RemoveKnowledgeObjectRelationCommand(
            organization_id=organization_id,
            relation_id=relation_id,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
