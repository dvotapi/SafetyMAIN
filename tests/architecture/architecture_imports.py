from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "venv",
}


@dataclass(frozen=True, slots=True)
class ImportViolation:
    source_file: Path
    imported_module: str
    rule: str


def iter_python_files(root: Path) -> Iterable[Path]:
    for source_file in root.rglob("*.py"):
        if any(part in IGNORED_DIRECTORY_NAMES for part in source_file.parts):
            continue
        yield source_file


def extract_imports(source_file: Path) -> tuple[str, ...]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    return tuple(imports)


def find_forbidden_imports(
    root: Path,
    *,
    forbidden_prefixes: Sequence[str],
    rule: str,
) -> tuple[ImportViolation, ...]:
    violations: list[ImportViolation] = []

    for source_file in iter_python_files(root):
        for imported_module in extract_imports(source_file):
            if _matches_forbidden_prefix(imported_module, forbidden_prefixes):
                violations.append(
                    ImportViolation(
                        source_file=source_file,
                        imported_module=imported_module,
                        rule=rule,
                    )
                )

    return tuple(violations)


def assert_no_forbidden_imports(
    root: Path,
    *,
    forbidden_prefixes: Sequence[str],
    rule: str,
) -> None:
    violations = find_forbidden_imports(
        root,
        forbidden_prefixes=forbidden_prefixes,
        rule=rule,
    )

    if not violations:
        return

    formatted_violations = "\n".join(
        f"- {violation.source_file}: forbidden import "
        f"`{violation.imported_module}` violates {violation.rule}"
        for violation in violations
    )
    raise AssertionError(f"Architecture dependency violations found:\n{formatted_violations}")


@dataclass(frozen=True, slots=True)
class MethodCallViolation:
    source_file: Path
    method_name: str
    rule: str


def find_forbidden_method_calls(
    root: Path,
    *,
    forbidden_methods: Sequence[str],
    rule: str,
) -> tuple[MethodCallViolation, ...]:
    violations: list[MethodCallViolation] = []

    for source_file in iter_python_files(root):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in forbidden_methods:
                continue
            violations.append(
                MethodCallViolation(
                    source_file=source_file,
                    method_name=node.func.attr,
                    rule=rule,
                )
            )

    return tuple(violations)


def assert_no_forbidden_method_calls(
    root: Path,
    *,
    forbidden_methods: Sequence[str],
    rule: str,
) -> None:
    violations = find_forbidden_method_calls(
        root,
        forbidden_methods=forbidden_methods,
        rule=rule,
    )
    if not violations:
        return

    formatted_violations = "\n".join(
        f"- {violation.source_file}: forbidden call `{violation.method_name}()` "
        f"violates {violation.rule}"
        for violation in violations
    )
    raise AssertionError(f"Architecture dependency violations found:\n{formatted_violations}")


@dataclass(frozen=True, slots=True)
class NameAssignmentViolation:
    source_file: Path
    assigned_name: str
    rule: str


def find_forbidden_name_assignments(
    root: Path,
    *,
    forbidden_names: Sequence[str],
    rule: str,
) -> tuple[NameAssignmentViolation, ...]:
    violations: list[NameAssignmentViolation] = []

    for source_file in iter_python_files(root):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in forbidden_names:
                    violations.append(
                        NameAssignmentViolation(
                            source_file=source_file,
                            assigned_name=target.id,
                            rule=rule,
                        )
                    )

    return tuple(violations)


def assert_no_forbidden_name_assignments(
    root: Path,
    *,
    forbidden_names: Sequence[str],
    rule: str,
) -> None:
    violations = find_forbidden_name_assignments(
        root,
        forbidden_names=forbidden_names,
        rule=rule,
    )
    if not violations:
        return

    formatted_violations = "\n".join(
        f"- {violation.source_file}: forbidden assignment `{violation.assigned_name}` "
        f"violates {violation.rule}"
        for violation in violations
    )
    raise AssertionError(f"Architecture dependency violations found:\n{formatted_violations}")


def _matches_forbidden_prefix(
    imported_module: str,
    forbidden_prefixes: Sequence[str],
) -> bool:
    return any(
        imported_module == prefix or imported_module.startswith(f"{prefix}.")
        for prefix in forbidden_prefixes
    )


@dataclass(frozen=True, slots=True)
class RequirePermissionViolation:
    source_file: Path
    handler_name: str
    call_count: int
    rule: str


_ROUTER_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})


def _is_router_route_decorator(decorator: ast.expr) -> bool:
    if not isinstance(decorator, ast.Call):
        return False
    func = decorator.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in _ROUTER_HTTP_METHODS:
        return False
    return isinstance(func.value, ast.Name) and func.value.id == "router"


def _count_require_permission_calls(function_node: ast.FunctionDef) -> int:
    count = 0
    for node in ast.walk(function_node):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "require_permission":
            count += 1
    return count


def find_route_handlers_with_multiple_require_permission(
    root: Path,
) -> tuple[RequirePermissionViolation, ...]:
    violations: list[RequirePermissionViolation] = []

    for source_file in iter_python_files(root):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            if not any(_is_router_route_decorator(decorator) for decorator in node.decorator_list):
                continue
            call_count = _count_require_permission_calls(node)
            if call_count > 1:
                violations.append(
                    RequirePermissionViolation(
                        source_file=source_file,
                        handler_name=node.name,
                        call_count=call_count,
                        rule=(
                            "Each API route handler must use at most one "
                            "require_permission() dependency to prevent duplicate "
                            "permission-denial audit events."
                        ),
                    )
                )

    return tuple(violations)


def assert_at_most_one_require_permission_per_route_handler(root: Path) -> None:
    violations = find_route_handlers_with_multiple_require_permission(root)
    if not violations:
        return

    formatted_violations = "\n".join(
        f"- {violation.source_file}:{violation.handler_name} uses "
        f"`require_permission()` {violation.call_count} times; "
        f"{violation.rule}"
        for violation in violations
    )
    raise AssertionError(f"Architecture dependency violations found:\n{formatted_violations}")
