from __future__ import annotations

from pathlib import Path

import pytest

from tests.architecture.architecture_imports import (
    assert_at_most_one_require_permission_per_route_handler,
    assert_no_forbidden_imports,
    find_forbidden_imports,
    find_route_handlers_with_multiple_require_permission,
)


def test_helper_detects_domain_importing_infrastructure(tmp_path: Path) -> None:
    source_file = tmp_path / "domain_service.py"
    source_file.write_text(
        "from backend.core.infrastructure.persistence import adapter\n",
        encoding="utf-8",
    )

    violations = find_forbidden_imports(
        tmp_path,
        forbidden_prefixes=("backend.core.infrastructure",),
        rule="domain must not import infrastructure",
    )

    assert len(violations) == 1
    assert violations[0].source_file == source_file
    assert violations[0].imported_module == "backend.core.infrastructure.persistence"


def test_helper_detects_application_importing_infrastructure(tmp_path: Path) -> None:
    source_file = tmp_path / "handler.py"
    source_file.write_text(
        "import backend.core.infrastructure.persistence.in_memory\n",
        encoding="utf-8",
    )

    violations = find_forbidden_imports(
        tmp_path,
        forbidden_prefixes=("backend.core.infrastructure",),
        rule="application must not import infrastructure",
    )

    assert len(violations) == 1
    assert violations[0].source_file == source_file
    assert (
        violations[0].imported_module
        == "backend.core.infrastructure.persistence.in_memory"
    )


def test_helper_detects_contract_importing_concrete_infrastructure(
    tmp_path: Path,
) -> None:
    source_file = tmp_path / "unit_of_work.py"
    source_file.write_text(
        "from backend.core.infrastructure.persistence.in_memory import InMemoryUnitOfWork\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError) as exc_info:
        assert_no_forbidden_imports(
            tmp_path,
            forbidden_prefixes=("backend.core.infrastructure",),
            rule="contracts must not import concrete adapters",
        )

    message = str(exc_info.value)
    assert str(source_file) in message
    assert "backend.core.infrastructure.persistence.in_memory" in message
    assert "contracts must not import concrete adapters" in message


def test_helper_allows_valid_inward_dependencies(tmp_path: Path) -> None:
    source_file = tmp_path / "adapter.py"
    source_file.write_text(
        "from backend.core.domain.entities.knowledge_object import KnowledgeObject\n"
        "from backend.core.contracts.unit_of_work import UnitOfWorkContract\n",
        encoding="utf-8",
    )

    assert_no_forbidden_imports(
        tmp_path,
        forbidden_prefixes=("backend.core.infrastructure",),
        rule="valid inward dependencies should pass",
    )


def test_helper_detects_multiple_require_permission_on_one_route_handler(
    tmp_path: Path,
) -> None:
    source_file = tmp_path / "routes.py"
    source_file.write_text(
        """
from typing import Annotated

from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("")
def list_items(
    _read: Annotated[object, Depends(require_permission("a"))],
    _write: Annotated[object, Depends(require_permission("b"))],
) -> None:
    return None


def require_permission(_permission: str):
    def _dependency() -> None:
        return None

    return _dependency
""",
        encoding="utf-8",
    )

    violations = find_route_handlers_with_multiple_require_permission(tmp_path)

    assert len(violations) == 1
    assert violations[0].handler_name == "list_items"
    assert violations[0].call_count == 2

    with pytest.raises(AssertionError):
        assert_at_most_one_require_permission_per_route_handler(tmp_path)
