"""Panel de estado general del servidor."""

from rich.panel import Panel
from rich.table import Table


def build_server_panel() -> Panel:
    """Construye el panel de estado del servidor."""

    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold")
    table.add_column()

    table.add_row("Host", "N/D")
    table.add_row("MediaMTX", "N/D")
    table.add_row("API", "N/D")
    table.add_row("Snapshot", "N/D")
    table.add_row("Calidad", "N/D")

    return Panel(
        table,
        title="SERVER",
        border_style="blue",
    )
