from __future__ import annotations

from pathlib import Path

from tests.architecture.architecture_imports import assert_no_forbidden_imports


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_ROOT = PROJECT_ROOT / "backend" / "core" / "domain"


def test_domain_layer_does_not_depend_on_outer_layers() -> None:
    assert_no_forbidden_imports(
        DOMAIN_ROOT,
        forbidden_prefixes=(
            "backend.core.application",
            "backend.core.infrastructure",
            "backend.api",
            "backend.bootstrap",
            "fastapi",
            "starlette",
            "sqlalchemy",
            "redis",
            "minio",
        ),
        rule="Domain layer must not depend on application, infrastructure, or API modules.",
    )
