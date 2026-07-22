"""Pruebas de la tabla de streams del monitor NOC."""

from rich.table import Table

from app.dashboard.tables.paths import build_paths_table


def test_build_paths_table_returns_table() -> None:
    table = build_paths_table()

    assert isinstance(table, Table)


def test_paths_table_contains_expected_columns() -> None:
    table = build_paths_table()

    column_names = [column.header for column in table.columns]

    assert column_names == [
        "Path",
        "Estado",
        "Readers",
        "Entrada",
        "Salida",
        "Calidad",
        "Fuente",
    ]
