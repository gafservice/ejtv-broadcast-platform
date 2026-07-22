"""Panel inferior del monitor NOC."""

from rich.align import Align
from rich.panel import Panel
from rich.text import Text


def build_footer_panel() -> Panel:
    """Construye el pie principal del dashboard."""

    text = Text(
        "MISSION-021 · Dashboard Architecture · Datos aún no conectados",
        justify="center",
        style="dim",
    )

    return Panel(
        Align.center(text),
        border_style="cyan",
    )
