"""Renderizador principal del dashboard."""

from rich.layout import Layout

from app.dashboard.models import DashboardData
from app.dashboard.renderers.path_table_renderer import PathTableRenderer
from app.dashboard.renderers.server_panel_renderer import (
    ServerPanelRenderer,
)
from app.dashboard.renderers.session_panel_renderer import (
    SessionPanelRenderer,
)
from app.dashboard.renderers.streaming_health_renderer import (
    StreamingHealthRenderer,
)
from app.dashboard.renderers.streaming_panel_renderer import (
    StreamingPanelRenderer,
)
from app.dashboard.renderers.system_panel_renderer import (
    SystemPanelRenderer,
)


class DashboardRenderer:
    """Ensambla los componentes visuales del dashboard."""

    def __init__(self) -> None:
        self._server_renderer = ServerPanelRenderer()
        self._streaming_renderer = StreamingPanelRenderer()
        self._session_renderer = SessionPanelRenderer()
        self._health_renderer = StreamingHealthRenderer()
        self._system_renderer = SystemPanelRenderer()
        self._path_table_renderer = PathTableRenderer()

    def render(self, data: DashboardData) -> Layout:
        """Convierte DashboardData en un layout completo de Rich."""

        layout = Layout(name="dashboard")

        layout.split_column(
            Layout(name="summary", size=18),
            Layout(name="paths"),
        )

        layout["summary"].split_column(
            Layout(name="summary_top", size=8),
            Layout(name="summary_bottom", size=10),
        )

        layout["summary_top"].split_row(
            Layout(name="server"),
            Layout(name="streaming"),
            Layout(name="health"),
        )

        if data.sessions is not None:
            layout["summary_bottom"].split_row(
                Layout(name="system"),
                Layout(name="sessions"),
            )
        else:
            layout["summary_bottom"].split_row(
                Layout(name="system"),
            )

        layout["server"].update(
            self._server_renderer.render(data.server)
        )

        layout["streaming"].update(
            self._streaming_renderer.render(data.streaming)
        )

        layout["health"].update(
            self._health_renderer.render(data.health)
        )

        if data.system is not None:
            layout["system"].update(
                self._system_renderer.render(data.system)
            )

        if data.sessions is not None:
            layout["sessions"].update(
                self._session_renderer.render(data.sessions)
            )

        layout["paths"].update(
            self._path_table_renderer.render(data.paths)
        )

        return layout
