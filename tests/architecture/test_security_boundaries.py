from __future__ import annotations

from pathlib import Path

from tests.architecture.architecture_imports import (
    assert_no_forbidden_imports,
    assert_no_forbidden_method_calls,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_ROOT = PROJECT_ROOT / "backend" / "core" / "application"
DOMAIN_ROOT = PROJECT_ROOT / "backend" / "core" / "domain"
API_ROUTERS_ROOT = PROJECT_ROOT / "backend" / "api" / "routers"


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
