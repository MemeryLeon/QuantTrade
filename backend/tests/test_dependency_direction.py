from __future__ import annotations

import ast
from pathlib import Path


FORBIDDEN_DOMAIN_IMPORTS = {
    "akshare",
    "fastapi",
    "ib_insync",
    "ibapi",
    "redis",
    "sqlalchemy",
}


def test_domain_layer_does_not_import_frameworks_or_sdks() -> None:
    domain_root = Path(__file__).resolve().parents[1] / "app" / "domains"
    violations: list[str] = []

    for path in domain_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            imported_module = _imported_module(node)
            if imported_module is None:
                continue
            top_level = imported_module.split(".", 1)[0]
            if top_level in FORBIDDEN_DOMAIN_IMPORTS:
                violations.append(f"{path.name}: {imported_module}")

    assert violations == []


def _imported_module(node: ast.AST) -> str | None:
    if isinstance(node, ast.Import):
        return node.names[0].name
    if isinstance(node, ast.ImportFrom):
        return node.module
    return None

