"""Tabla de streams y paths del monitor NOC."""

from rich.table import Table


def build_paths_table() -> Table:
    """Construye la tabla inicial de paths."""

    table = Table(
        title="ACTIVE STREAMS",
        expand=True,
        show_lines=True,
        header_style="bold cyan",
    )

    table.add_column("Path")
    table.add_column("Estado")
    table.add_column("Readers", justify="right")
    table.add_column("Entrada", justify="right")
    table.add_column("Salida", justify="right")
    table.add_column("Calidad")
    table.add_column("Fuente")

    table.add_row(
        "Sin datos",
        "N/D",
        "0",
        "0 bps",
        "0 bps",
        "N/D",
        "N/D",
    )

    return table
