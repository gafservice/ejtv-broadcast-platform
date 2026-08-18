"""Renderizador principal del dashboard."""

from rich.layout import Layout

from app.dashboard.models import DashboardData
from app.dashboard.renderers.active_connections_panel_renderer import (
    ActiveConnectionsPanelRenderer,
)
from app.dashboard.renderers.network_interfaces_panel_renderer import (
    NetworkInterfacesPanelRenderer,
)
from app.dashboard.renderers.node_health_panel_renderer import (
    NodeHealthPanelRenderer,
)
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
        self._active_connections_renderer = (
            ActiveConnectionsPanelRenderer()
        )
        self._health_renderer = StreamingHealthRenderer()
        self._system_renderer = SystemPanelRenderer()
        self._network_interfaces_renderer = (
            NetworkInterfacesPanelRenderer()
        )
        self._node_health_renderer = (
            NodeHealthPanelRenderer()
        )
        self._path_table_renderer = PathTableRenderer()

    def render(self, data: DashboardData) -> Layout:
        """Convierte DashboardData en un layout completo de Rich."""

        layout = Layout(name="dashboard")

        if (
            data.network_interfaces is not None
            and data.active_connections is not None
        ):
            layout.split_column(
                Layout(name="summary", size=22),
                Layout(name="network_interfaces", size=11),
                Layout(name="active_connections", size=12),
                Layout(name="paths"),
            )

        elif data.network_interfaces is not None:
            layout.split_column(
                Layout(name="summary", size=22),
                Layout(name="network_interfaces", size=11),
                Layout(name="paths"),
            )

        elif data.active_connections is not None:
            layout.split_column(
                Layout(name="summary", size=22),
                Layout(name="active_connections", size=12),
                Layout(name="paths"),
            )

        else:
            layout.split_column(
                Layout(name="summary", size=22),
                Layout(name="paths"),
            )

        layout["summary"].split_column(
            Layout(name="summary_top", size=8),
            Layout(name="summary_bottom", size=14),
        )

        layout["summary_top"].split_row(
            Layout(name="server"),
            Layout(name="streaming"),
            Layout(name="health"),
            Layout(name="node_health"),
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

        layout["node_health"].update(
            self._node_health_renderer.render(
                data.node_health
            )
        )

        if data.system is not None:
            layout["system"].update(
                self._system_renderer.render(data.system)
            )

        if data.sessions is not None:
            layout["sessions"].update(
                self._session_renderer.render(data.sessions)
            )

        if data.network_interfaces is not None:
            layout["network_interfaces"].update(
                self._network_interfaces_renderer.render(
                    data.network_interfaces
                )
            )

        if data.active_connections is not None:
            layout["active_connections"].update(
                self._active_connections_renderer.render(
                    data.active_connections
                )
            )

        layout["paths"].update(
            self._path_table_renderer.render(data.paths)
        )

        return layout
