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


def _matches_forbidden_prefix(
    imported_module: str,
    forbidden_prefixes: Sequence[str],
) -> bool:
    return any(
        imported_module == prefix or imported_module.startswith(f"{prefix}.")
        for prefix in forbidden_prefixes
    )
