"""Panel de métricas del sistema operativo."""

from rich.panel import Panel
from rich.table import Table


def build_system_panel() -> Panel:
    """Construye el panel de métricas del sistema."""

    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold")
    table.add_column()

    table.add_row("CPU", "N/D")
    table.add_row("RAM", "N/D")
    table.add_row("Disco", "N/D")
    table.add_row("Uptime", "N/D")
    table.add_row("Load Average", "N/D")

    return Panel(
        table,
        title="SYSTEM",
        border_style="blue",
    )
