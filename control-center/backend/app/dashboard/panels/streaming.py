"""Panel de resumen del servicio de streaming."""

from rich.panel import Panel
from rich.table import Table


def build_streaming_panel() -> Panel:
    """Construye el panel resumen de streaming."""

    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold")
    table.add_column()

    table.add_row("Paths activos", "0")
    table.add_row("Readers", "0")
    table.add_row("Entrada", "0 bps")
    table.add_row("Salida", "0 bps")
    table.add_row("Calidad", "N/D")

    return Panel(
        table,
        title="STREAMING",
        border_style="blue",
    )
