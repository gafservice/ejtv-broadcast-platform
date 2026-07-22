"""Panel de encabezado del monitor NOC."""

from rich.align import Align
from rich.panel import Panel
from rich.text import Text


def build_header_panel() -> Panel:
    """Construye el encabezado principal del dashboard."""

    title = Text(
        "CONTROL CENTER · NETWORK OPERATIONS CENTER",
        justify="center",
        style="bold white",
    )

    subtitle = Text(
        "Live Operations Monitor",
        justify="center",
        style="cyan",
    )

    content = Text.assemble(
        title,
        "\n",
        subtitle,
    )

    return Panel(
        Align.center(content, vertical="middle"),
        border_style="cyan",
    )
