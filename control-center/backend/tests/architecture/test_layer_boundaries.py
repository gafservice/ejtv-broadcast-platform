"""Pruebas que protegen los límites de la arquitectura."""

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROTECTED_DIRECTORIES = (
    PROJECT_ROOT / "app" / "api" / "v1",
    PROJECT_ROOT / "app" / "services",
    PROJECT_ROOT / "app" / "domain",
)

FORBIDDEN_STANDARD_MODULES = {
    "platform",
    "socket",
    "subprocess",
}

FORBIDDEN_INTERNAL_PREFIXES = (
    "app.adapters.linux",
)


def python_files() -> list[Path]:
    """Retorna los archivos Python de las capas protegidas."""

    files: list[Path] = []

    for directory in PROTECTED_DIRECTORIES:
        files.extend(directory.rglob("*.py"))

    return files


def imported_modules(path: Path) -> set[str]:
    """Extrae los módulos importados por un archivo Python."""

    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)

        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)

    return modules


def test_protected_layers_do_not_access_linux_adapter() -> None:
    violations: list[str] = []

    for path in python_files():
        for module in imported_modules(path):
            if module.startswith(FORBIDDEN_INTERNAL_PREFIXES):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} importa {module}"
                )

    assert not violations, "\n".join(violations)


def test_protected_layers_do_not_import_system_modules() -> None:
    violations: list[str] = []

    for path in python_files():
        for module in imported_modules(path):
            root_module = module.split(".", maxsplit=1)[0]

            if root_module in FORBIDDEN_STANDARD_MODULES:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} importa {module}"
                )

    assert not violations, "\n".join(violations)


def test_linux_adapter_is_only_composed_in_dependencies() -> None:
    dependencies_file = PROJECT_ROOT / "app" / "api" / "dependencies.py"

    modules = imported_modules(dependencies_file)

    assert "app.adapters.linux.linux_system_adapter" in modules
