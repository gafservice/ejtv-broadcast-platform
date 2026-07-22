"""Renderizador principal del dashboard."""

from rich.layout import Layout

from app.dashboard.models import DashboardData
from app.dashboard.renderers.path_table_renderer import PathTableRenderer
from app.dashboard.renderers.server_panel_renderer import (
    ServerPanelRenderer,
)
from app.dashboard.renderers.streaming_panel_renderer import (
    StreamingPanelRenderer,
)


class DashboardRenderer:
    """Ensambla los componentes visuales del dashboard."""

    def __init__(self) -> None:
        self._server_renderer = ServerPanelRenderer()
        self._streaming_renderer = StreamingPanelRenderer()
        self._path_table_renderer = PathTableRenderer()

    def render(self, data: DashboardData) -> Layout:
        """Convierte DashboardData en un layout completo de Rich."""

        layout = Layout(name="dashboard")

        layout.split_column(
            Layout(name="summary", size=8),
            Layout(name="paths"),
        )

        layout["summary"].split_row(
            Layout(name="server"),
            Layout(name="streaming"),
        )

        layout["server"].update(
            self._server_renderer.render(data.server)
        )

        layout["streaming"].update(
            self._streaming_renderer.render(data.streaming)
        )

        layout["paths"].update(
            self._path_table_renderer.render(data.paths)
        )

        return layout
