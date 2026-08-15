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
AUTH_LOGOUT = "auth_logout"
AUTH_SESSION = "auth_session"

CREATE_USER = "create_user"
LIST_USERS = "list_users"
GET_USER = "get_user"
UPDATE_USER = "update_user"
ACTIVATE_USER = "activate_user"
DEACTIVATE_USER = "deactivate_user"

CREATE_ORGANIZATION = "create_organization"
LIST_ORGANIZATIONS = "list_organizations"
GET_ORGANIZATION = "get_organization"
UPDATE_ORGANIZATION = "update_organization"
ACTIVATE_ORGANIZATION = "activate_organization"
DEACTIVATE_ORGANIZATION = "deactivate_organization"

CREATE_MEMBERSHIP = "create_membership"
LIST_MEMBERSHIPS = "list_memberships"
GET_MEMBERSHIP = "get_membership"
UPDATE_MEMBERSHIP_ROLE = "update_membership_role"
ACTIVATE_MEMBERSHIP = "activate_membership"
DEACTIVATE_MEMBERSHIP = "deactivate_membership"

CREATE_INVITATION = "create_invitation"
LIST_INVITATIONS = "list_invitations"
GET_INVITATION = "get_invitation"
REVOKE_INVITATION = "revoke_invitation"
REISSUE_INVITATION = "reissue_invitation"
ACCEPT_INVITATION = "accept_invitation"
LIST_AUDIT_EVENTS = "list_audit_events"
GET_AUDIT_EVENT = "get_audit_event"
VERIFY_AUDIT_CHAIN_INTEGRITY = "verify_audit_chain_integrity"

CREATE_HAZARD = "create_hazard"
LIST_HAZARDS = "list_hazards"
GET_HAZARD = "get_hazard"
UPDATE_HAZARD = "update_hazard"
ACTIVATE_HAZARD = "activate_hazard"
ARCHIVE_HAZARD = "archive_hazard"
RESTORE_HAZARD = "restore_hazard"

CREATE_RISK_ASSESSMENT = "create_risk_assessment"
LIST_RISK_ASSESSMENTS = "list_risk_assessments"
GET_RISK_ASSESSMENT = "get_risk_assessment"
UPDATE_RISK_ASSESSMENT = "update_risk_assessment"
APPROVE_RISK_ASSESSMENT = "approve_risk_assessment"
ARCHIVE_RISK_ASSESSMENT = "archive_risk_assessment"

CREATE_RISK_CONTROL = "create_risk_control"
LIST_RISK_CONTROLS = "list_risk_controls"
GET_RISK_CONTROL = "get_risk_control"
UPDATE_RISK_CONTROL = "update_risk_control"
ASSIGN_RISK_CONTROL_OWNER = "assign_risk_control_owner"
PLAN_RISK_CONTROL = "plan_risk_control"
START_RISK_CONTROL_IMPLEMENTATION = "start_risk_control_implementation"
UPDATE_RISK_CONTROL_PROGRESS = "update_risk_control_progress"
ADD_RISK_CONTROL_EVIDENCE = "add_risk_control_evidence"
COMPLETE_RISK_CONTROL_IMPLEMENTATION = "complete_risk_control_implementation"
RECORD_RISK_CONTROL_VERIFICATION = "record_risk_control_verification"
SCHEDULE_RISK_CONTROL_REVIEW = "schedule_risk_control_review"
COMPLETE_RISK_CONTROL_REVIEW = "complete_risk_control_review"
SUSPEND_RISK_CONTROL = "suspend_risk_control"
RESUME_RISK_CONTROL = "resume_risk_control"
SUPERSEDE_RISK_CONTROL = "supersede_risk_control"
ARCHIVE_RISK_CONTROL = "archive_risk_control"
CANCEL_RISK_CONTROL = "cancel_risk_control"
MATERIALIZE_RISK_ASSESSMENT_CONTROLS = "materialize_risk_assessment_controls"

STABLE_OPERATION_IDS: frozenset[str] = frozenset(
    {
        HEALTH,
        READINESS,
        AUTH_LOGIN,
        AUTH_REFRESH,
        AUTH_LOGOUT,
        AUTH_SESSION,
        CREATE_USER,
        LIST_USERS,
        GET_USER,
        UPDATE_USER,
        ACTIVATE_USER,
        DEACTIVATE_USER,
        CREATE_ORGANIZATION,
        LIST_ORGANIZATIONS,
        GET_ORGANIZATION,
        UPDATE_ORGANIZATION,
        ACTIVATE_ORGANIZATION,
        DEACTIVATE_ORGANIZATION,
        CREATE_MEMBERSHIP,
        LIST_MEMBERSHIPS,
        GET_MEMBERSHIP,
        UPDATE_MEMBERSHIP_ROLE,
        ACTIVATE_MEMBERSHIP,
        DEACTIVATE_MEMBERSHIP,
        CREATE_INVITATION,
        LIST_INVITATIONS,
        GET_INVITATION,
        REVOKE_INVITATION,
        REISSUE_INVITATION,
        ACCEPT_INVITATION,
        LIST_AUDIT_EVENTS,
        GET_AUDIT_EVENT,
        VERIFY_AUDIT_CHAIN_INTEGRITY,
        CREATE_HAZARD,
        LIST_HAZARDS,
        GET_HAZARD,
        UPDATE_HAZARD,
        ACTIVATE_HAZARD,
        ARCHIVE_HAZARD,
        RESTORE_HAZARD,
        CREATE_RISK_ASSESSMENT,
        LIST_RISK_ASSESSMENTS,
        GET_RISK_ASSESSMENT,
        UPDATE_RISK_ASSESSMENT,
        APPROVE_RISK_ASSESSMENT,
        ARCHIVE_RISK_ASSESSMENT,
        CREATE_RISK_CONTROL,
        LIST_RISK_CONTROLS,
        GET_RISK_CONTROL,
        UPDATE_RISK_CONTROL,
        ASSIGN_RISK_CONTROL_OWNER,
        PLAN_RISK_CONTROL,
        START_RISK_CONTROL_IMPLEMENTATION,
        UPDATE_RISK_CONTROL_PROGRESS,
        ADD_RISK_CONTROL_EVIDENCE,
        COMPLETE_RISK_CONTROL_IMPLEMENTATION,
        RECORD_RISK_CONTROL_VERIFICATION,
        SCHEDULE_RISK_CONTROL_REVIEW,
        COMPLETE_RISK_CONTROL_REVIEW,
        SUSPEND_RISK_CONTROL,
        RESUME_RISK_CONTROL,
        SUPERSEDE_RISK_CONTROL,
        ARCHIVE_RISK_CONTROL,
        CANCEL_RISK_CONTROL,
        MATERIALIZE_RISK_ASSESSMENT_CONTROLS,
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
