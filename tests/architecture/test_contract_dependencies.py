from __future__ import annotations

from pathlib import Path

from tests.architecture.architecture_imports import assert_no_forbidden_imports


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_ROOT = PROJECT_ROOT / "backend" / "core" / "contracts"


def test_contracts_do_not_depend_on_concrete_infrastructure() -> None:
    assert_no_forbidden_imports(
        CONTRACTS_ROOT,
        forbidden_prefixes=(
            "backend.core.infrastructure",
            "backend.api",
            "backend.bootstrap",
            "fastapi",
            "starlette",
            "sqlalchemy",
            "redis",
            "minio",
        ),
        rule="Contracts and ports must not depend on concrete adapters or API modules.",
    )
