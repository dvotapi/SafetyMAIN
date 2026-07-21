from __future__ import annotations

# Stable OpenAPI operation identifiers for generated clients.

HEALTH = "health"
READINESS = "readiness"

CREATE_KNOWLEDGE_OBJECT = "create_knowledge_object"
SEARCH_KNOWLEDGE_OBJECTS = "search_knowledge_objects"
GET_KNOWLEDGE_OBJECT = "get_knowledge_object"
UPDATE_KNOWLEDGE_OBJECT = "update_knowledge_object"
ARCHIVE_KNOWLEDGE_OBJECT = "archive_knowledge_object"
RESTORE_KNOWLEDGE_OBJECT = "restore_knowledge_object"
DELETE_KNOWLEDGE_OBJECT = "delete_knowledge_object"
GET_KNOWLEDGE_OBJECT_HISTORY = "get_knowledge_object_history"
GET_OUTGOING_RELATIONS = "get_outgoing_relations"
GET_INCOMING_RELATIONS = "get_incoming_relations"
GET_CONNECTED_KNOWLEDGE_OBJECTS = "get_connected_knowledge_objects"

CREATE_KNOWLEDGE_OBJECT_RELATION = "create_knowledge_object_relation"
GET_KNOWLEDGE_OBJECT_RELATION = "get_knowledge_object_relation"
DELETE_KNOWLEDGE_OBJECT_RELATION = "delete_knowledge_object_relation"

AUTH_LOGIN = "auth_login"
AUTH_REFRESH = "auth_refresh"

CREATE_USER = "create_user"
LIST_USERS = "list_users"
GET_USER = "get_user"
UPDATE_USER = "update_user"
ACTIVATE_USER = "activate_user"
DEACTIVATE_USER = "deactivate_user"

STABLE_OPERATION_IDS: frozenset[str] = frozenset(
    {
        HEALTH,
        READINESS,
        AUTH_LOGIN,
        AUTH_REFRESH,
        CREATE_USER,
        LIST_USERS,
        GET_USER,
        UPDATE_USER,
        ACTIVATE_USER,
        DEACTIVATE_USER,
        CREATE_KNOWLEDGE_OBJECT,
        SEARCH_KNOWLEDGE_OBJECTS,
        GET_KNOWLEDGE_OBJECT,
        UPDATE_KNOWLEDGE_OBJECT,
        ARCHIVE_KNOWLEDGE_OBJECT,
        RESTORE_KNOWLEDGE_OBJECT,
        DELETE_KNOWLEDGE_OBJECT,
        GET_KNOWLEDGE_OBJECT_HISTORY,
        GET_OUTGOING_RELATIONS,
        GET_INCOMING_RELATIONS,
        GET_CONNECTED_KNOWLEDGE_OBJECTS,
        CREATE_KNOWLEDGE_OBJECT_RELATION,
        GET_KNOWLEDGE_OBJECT_RELATION,
        DELETE_KNOWLEDGE_OBJECT_RELATION,
    }
)
