from __future__ import annotations

from pathlib import Path

from tests.architecture.architecture_imports import (
    assert_no_forbidden_imports,
    assert_no_forbidden_method_calls,
    assert_no_forbidden_name_assignments,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_ROOT = PROJECT_ROOT / "backend" / "core" / "application"
DOMAIN_ROOT = PROJECT_ROOT / "backend" / "core" / "domain"
API_ROUTERS_ROOT = PROJECT_ROOT / "backend" / "api" / "routers"
KNOWLEDGE_OBJECTS_ROUTER = API_ROUTERS_ROOT / "knowledge_objects.py"
RELATIONS_ROUTER = API_ROUTERS_ROOT / "relations.py"
ADMIN_USERS_ROUTER = API_ROUTERS_ROOT / "admin_users.py"
ADMIN_ORGANIZATIONS_ROUTER = API_ROUTERS_ROOT / "admin_organizations.py"
ADMIN_MEMBERSHIPS_ROUTER = API_ROUTERS_ROOT / "admin_memberships.py"
ADMIN_INVITATIONS_ROUTER = API_ROUTERS_ROOT / "admin_invitations.py"
BUSINESS_ROUTERS = (
    KNOWLEDGE_OBJECTS_ROUTER,
    RELATIONS_ROUTER,
    ADMIN_USERS_ROUTER,
    ADMIN_ORGANIZATIONS_ROUTER,
    ADMIN_MEMBERSHIPS_ROUTER,
    ADMIN_INVITATIONS_ROUTER,
)


def test_application_security_modules_do_not_import_jwt_or_fastapi() -> None:
    for root in (
        APPLICATION_ROOT / "authorization",
        APPLICATION_ROOT / "context",
        APPLICATION_ROOT / "tenant",
    ):
        assert_no_forbidden_imports(
            root,
            forbidden_prefixes=(
                "jwt",
                "fastapi",
                "starlette",
                "backend.core.infrastructure",
            ),
            rule="Application security modules must not depend on JWT, FastAPI, or Infrastructure.",
        )


def test_domain_identity_modules_do_not_import_jwt_or_fastapi() -> None:
    for root in (
        DOMAIN_ROOT / "entities",
        DOMAIN_ROOT / "value_objects",
    ):
        assert_no_forbidden_imports(
            root,
            forbidden_prefixes=(
                "jwt",
                "fastapi",
                "starlette",
                "backend.core.application",
                "backend.core.infrastructure",
                "backend.api",
            ),
            rule="Domain identity and authorization types must remain transport-free.",
        )


def test_business_routers_do_not_construct_authorization_services() -> None:
    assert_no_forbidden_imports(
        API_ROUTERS_ROOT,
        forbidden_prefixes=(
            "backend.core.application.authorization.authorization_service",
            "backend.core.infrastructure.auth.jwt_token_service",
        ),
        rule="API routers must consume authorization through dependencies, not concrete services.",
    )


def test_business_routers_do_not_call_membership_or_permission_evaluators_directly() -> None:
    assert_no_forbidden_method_calls(
        API_ROUTERS_ROOT,
        forbidden_methods=(
            "require_organization_access",
            "authorize_permission",
            "is_active_member",
        ),
        rule="Business routers must not invoke authorization services directly.",
    )


def test_business_routers_use_require_permission_dependency() -> None:
    for router_file in BUSINESS_ROUTERS:
        content = router_file.read_text(encoding="utf-8")
        assert "require_permission" in content
        assert "Depends(get_tenant_context)" not in content


def test_business_routers_do_not_resolve_roles_or_permissions_directly() -> None:
    assert_no_forbidden_imports(
        API_ROUTERS_ROOT,
        forbidden_prefixes=(
            "backend.core.domain.value_objects.role_permissions",
            "backend.core.application.authorization.authorization_service",
            "backend.core.application.authorization.permission_evaluator",
            "backend.core.application.authorization.role_permission_resolver",
        ),
        rule="Business routers must consume centralized permission policies only.",
    )


def test_business_routers_do_not_redefine_resource_permission_constants() -> None:
    assert_no_forbidden_name_assignments(
        API_ROUTERS_ROOT,
        forbidden_names=(
            "KNOWLEDGE_OBJECT_READ",
            "KNOWLEDGE_OBJECT_WRITE",
            "KNOWLEDGE_OBJECT_DELETE",
            "RELATION_READ",
            "RELATION_WRITE",
            "RELATION_DELETE",
        ),
        rule="Business routers must import reusable permission policies instead of redefining them.",
    )
