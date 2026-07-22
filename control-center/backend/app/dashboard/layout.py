"""Composición visual principal del monitor NOC."""

from rich.layout import Layout
from rich.panel import Panel

from app.dashboard.panels.footer import build_footer_panel
from app.dashboard.panels.header import build_header_panel
from app.dashboard.panels.server import build_server_panel
from app.dashboard.panels.streaming import build_streaming_panel
from app.dashboard.panels.system import build_system_panel
from app.dashboard.tables.paths import build_paths_table


def build_dashboard() -> Layout:
    """Construye el layout completo del monitor NOC."""

    root = Layout(name="root")

    root.split_column(
        Layout(name="header", size=5),
        Layout(name="summary", size=11),
        Layout(name="paths"),
        Layout(name="footer", size=3),
    )

    root["summary"].split_row(
        Layout(name="server"),
        Layout(name="streaming"),
        Layout(name="system"),
    )

    root["header"].update(build_header_panel())
    root["server"].update(build_server_panel())
    root["streaming"].update(build_streaming_panel())
    root["system"].update(build_system_panel())

    root["paths"].update(
        Panel(
            build_paths_table(),
            border_style="blue",
        )
    )

    root["footer"].update(build_footer_panel())

    return root
