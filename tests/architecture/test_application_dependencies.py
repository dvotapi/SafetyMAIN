from __future__ import annotations

from pathlib import Path

from tests.architecture.architecture_imports import assert_no_forbidden_imports


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APPLICATION_ROOT = PROJECT_ROOT / "backend" / "core" / "application"


def test_application_layer_does_not_depend_on_infrastructure() -> None:
    assert_no_forbidden_imports(
        APPLICATION_ROOT,
        forbidden_prefixes=(
            "backend.core.infrastructure",
            "fastapi",
            "sqlalchemy",
            "redis",
            "minio",
        ),
        rule="Application layer must depend on contracts, not concrete infrastructure.",
    )
