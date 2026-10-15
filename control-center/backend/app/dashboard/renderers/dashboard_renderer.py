"""Renderizador principal del dashboard."""

from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel

from app.dashboard.models import DashboardData
from app.dashboard.models.dashboard_navigation_state import (
    DashboardNavigationState,
    NavigablePanel,
)
from app.dashboard.models.panel_viewport import PanelViewport
from app.dashboard.services.incoming_vertical_geometry_policy import (
    IncomingVerticalGeometry,
)
from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
    IncomingDetailTabState,
)
from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
)
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)
from app.dashboard.renderers.active_alarms_panel_renderer import (
    ActiveAlarmsPanelRenderer,
)
from app.dashboard.renderers.capacity_panel_renderer import (
    CapacityPanelRenderer,
)
from app.dashboard.renderers.active_connections_panel_renderer import (
    ActiveConnectionsPanelRenderer,
)
from app.dashboard.renderers.network_interfaces_panel_renderer import (
    NetworkInterfacesPanelRenderer,
)
from app.dashboard.renderers.node_health_panel_renderer import (
    NodeHealthPanelRenderer,
)
from app.dashboard.renderers.platform_health_renderer import (
    PlatformHealthRenderer,
)
from app.dashboard.renderers.recent_events_panel_renderer import (
    RecentEventsPanelRenderer,
)
from app.dashboard.renderers.incoming_panel_renderer import (
    IncomingPanelRenderer,
)
from app.dashboard.renderers.incoming_signal_cards_renderer import (
    IncomingSignalCardsRenderer,
)
from app.dashboard.renderers.signal_detail_renderer import (
    SignalDetailRenderer,
)
from app.dashboard.renderers.incoming_signal_header_renderer import (
    IncomingSignalHeaderRenderer,
)
from app.dashboard.renderers.incoming_detail_tab_strip import (
    IncomingDetailTabStrip,
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
        self._capacity_renderer = CapacityPanelRenderer()
        self._active_connections_renderer = (
            ActiveConnectionsPanelRenderer()
        )
        self._active_alarms_renderer = (
            ActiveAlarmsPanelRenderer()
        )
        self._health_renderer = StreamingHealthRenderer()
        self._system_renderer = SystemPanelRenderer()
        self._network_interfaces_renderer = (
            NetworkInterfacesPanelRenderer()
        )
        self._node_health_renderer = (
            NodeHealthPanelRenderer()
        )
        self._platform_health_renderer = (
            PlatformHealthRenderer()
        )
        self._recent_events_renderer = (
            RecentEventsPanelRenderer()
        )
        self._incoming_panel_renderer = IncomingPanelRenderer()
        self._signal_detail_renderer = SignalDetailRenderer()
        self._incoming_signal_header_renderer = (
            IncomingSignalHeaderRenderer()
        )
        self._path_table_renderer = PathTableRenderer()

    def render(
        self,
        data: DashboardData,
        *,
        navigation_state: DashboardNavigationState | None = None,
        terminal_navigation_state: TerminalNavigationState | None = None,
        incoming_selection_state: IncomingSelectionState | None = None,
        incoming_detail_tab_state: IncomingDetailTabState | None = None,
        incoming_viewport: PanelViewport | None = None,
        incoming_presentation_mode: str = "full",
        incoming_visible_capacity: int | None = None,
        incoming_vertical_geometry: IncomingVerticalGeometry | None = None,
        terminal_width: int | None = None,
    ) -> Layout:
        """Convierte DashboardData en un layout completo de Rich."""

        if (
            navigation_state is not None
            and not isinstance(
                navigation_state,
                DashboardNavigationState,
            )
        ):
            raise TypeError(
                "navigation_state must be a "
                "DashboardNavigationState or None"
            )

        if (
            terminal_navigation_state is not None
            and not isinstance(
                terminal_navigation_state,
                TerminalNavigationState,
            )
        ):
            raise TypeError(
                "terminal_navigation_state must be a "
                "TerminalNavigationState or None"
            )

        layout = Layout(name="dashboard")

        sections = []

        if terminal_navigation_state is not None:
            sections.append(
                Layout(
                    Panel(
                        "VIEW: "
                        f"{terminal_navigation_state.active_view.name}",
                        title="TERMINAL",
                    ),
                    name="terminal_view",
                    size=3,
                )
            )

        if (
            terminal_navigation_state is not None
            and terminal_navigation_state.active_view
            is TerminalView.INCOMING
        ):
            sections.append(
                Layout(name="incoming")
            )

            layout.split_column(
                *sections
            )

            if incoming_vertical_geometry is None:
                list_height = None
                detail_height = (
                    12 if incoming_visible_capacity == 0 else 20
                )
            else:
                if not isinstance(
                    incoming_vertical_geometry,
                    IncomingVerticalGeometry,
                ):
                    raise TypeError(
                        "incoming_vertical_geometry must be an "
                        "IncomingVerticalGeometry or None"
                    )

                list_height = incoming_vertical_geometry.list_height
                detail_height = incoming_vertical_geometry.detail_height

            layout["incoming"].split_column(
                Layout(name="incoming_list", size=list_height),
                Layout(name="signal_detail", size=detail_height),
            )

            selected_path_name = (
                incoming_selection_state.selected_path_name
                if incoming_selection_state is not None
                else None
            )

            if incoming_visible_capacity == 0:
                layout["incoming_list"].update(
                    Panel(
                        "Insufficient terminal height. "
                        "Enlarge the terminal to display incoming signals.",
                        title="INCOMING SIGNALS",
                    )
                )
            else:
                layout["incoming_list"].update(
                    self._incoming_panel_renderer.render(
                        data.incoming,
                        selected_path_name=selected_path_name,
                        viewport=incoming_viewport,
                        presentation_mode=incoming_presentation_mode,
                    )
                )

            active_tab = (
                incoming_detail_tab_state.active_tab
                if incoming_detail_tab_state is not None
                else IncomingDetailTab.SIGNAL
            )

            if active_tab is IncomingDetailTab.SIGNAL:
                use_signal_cards_v2 = (
                    incoming_vertical_geometry is not None
                    and incoming_vertical_geometry.detail_height >= 20
                    and isinstance(data.incoming, IncomingPanelData)
                )

                if use_signal_cards_v2:
                    detail_panel = IncomingSignalCardsRenderer().render(
                        data.incoming,
                        selected_path_name=selected_path_name,
                    )
                else:
                    detail_panel = self._signal_detail_renderer.render(
                        data.incoming,
                        selected_path_name=selected_path_name,
                        compact=(
                            incoming_visible_capacity == 0
                            if incoming_vertical_geometry is None
                            else incoming_vertical_geometry.detail_height < 20
                        ),
                    )
            else:
                detail_panel = Panel(
                    (
                        "No incoming signal selected."
                        if selected_path_name is None
                        else (
                            f"Signal: {selected_path_name}\n"
                            "Metrics: N/A"
                        )
                    ),
                    title=f"{active_tab.name} DETAIL",
                )

            if active_tab is IncomingDetailTab.SIGNAL:
                detail_panel.title = (
                    self._incoming_signal_header_renderer.render(
                        data.incoming,
                        selected_path_name=selected_path_name,
                    )
                )

            if terminal_width is not None and terminal_width <= 0:
                raise ValueError("terminal_width must be positive")

            available_width = (
                max(1, terminal_width - 4)
                if terminal_width is not None
                else 80
            )

            tab_strip = IncomingDetailTabStrip.render(
                active_tab=active_tab,
                width=available_width,
            )

            if incoming_vertical_geometry is not None:
                detail_panel.renderable = Group(
                    tab_strip,
                    detail_panel.renderable,
                )
                detail_panel.subtitle = None
            else:
                detail_panel.subtitle = tab_strip

            layout["signal_detail"].update(detail_panel)

            return layout

        sections.append(
            Layout(name="summary", size=22)
        )

        if data.network_interfaces is not None:
            sections.append(
                Layout(
                    name="network_interfaces",
                    size=11,
                )
            )

        if data.capacity is not None:
            sections.append(
                Layout(
                    name="capacity",
                    size=9,
                )
            )

        if data.active_connections is not None:
            sections.append(
                Layout(
                    name="active_connections",
                    size=12,
                )
            )

        if data.active_alarms is not None:
            sections.append(
                Layout(
                    name="active_alarms",
                    size=9,
                )
            )

        if data.recent_events is not None:
            sections.append(
                Layout(
                    name="recent_events",
                    size=9,
                )
            )

        sections.append(
            Layout(name="paths")
        )

        layout.split_column(
            *sections
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
                Layout(name="platform_health"),
            )
        else:
            layout["summary_bottom"].split_row(
                Layout(name="system"),
                Layout(name="platform_health"),
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

        layout["platform_health"].update(
            self._platform_health_renderer.render(
                data.platform_health
            )
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

        if data.capacity is not None:
            layout["capacity"].update(
                self._capacity_renderer.render(
                    data.capacity
                )
            )

        if data.active_connections is not None:
            active_connections_panel = (
                self._active_connections_renderer.render(
                    data.active_connections
                )
            )

            self._decorate_navigable_panel(
                active_connections_panel,
                navigation_state=navigation_state,
                panel=NavigablePanel.ACTIVE_CONNECTIONS,
                total_items=data.active_connections.total_items,
                visible_items=len(
                    data.active_connections.connections
                ),
            )

            layout["active_connections"].update(
                active_connections_panel
            )

        if data.active_alarms is not None:
            active_alarms_panel = (
                self._active_alarms_renderer.render(
                    data.active_alarms
                )
            )

            self._decorate_navigable_panel(
                active_alarms_panel,
                navigation_state=navigation_state,
                panel=NavigablePanel.ACTIVE_ALARMS,
                total_items=data.active_alarms.total_items,
                visible_items=len(
                    data.active_alarms.alarms
                ),
            )

            layout["active_alarms"].update(
                active_alarms_panel
            )

        if data.recent_events is not None:
            recent_events_panel = (
                self._recent_events_renderer.render(
                    data.recent_events
                )
            )

            self._decorate_navigable_panel(
                recent_events_panel,
                navigation_state=navigation_state,
                panel=NavigablePanel.RECENT_EVENTS,
                total_items=data.recent_events.total_items,
                visible_items=len(
                    data.recent_events.events
                ),
            )

            layout["recent_events"].update(
                recent_events_panel
            )

        layout["paths"].update(
            self._path_table_renderer.render(data.paths)
        )

        return layout

    @staticmethod
    def _decorate_navigable_panel(
        rich_panel: Panel,
        *,
        navigation_state: DashboardNavigationState | None,
        panel: NavigablePanel,
        total_items: int | None,
        visible_items: int,
    ) -> None:
        """Añade foco y posición a un panel navegable."""

        if not isinstance(rich_panel, Panel):
            raise TypeError(
                "rich_panel must be a rich.panel.Panel"
            )

        if not isinstance(panel, NavigablePanel):
            raise TypeError(
                "panel must be a NavigablePanel"
            )

        if (
            isinstance(total_items, bool)
            or (
                total_items is not None
                and not isinstance(total_items, int)
            )
        ):
            raise TypeError(
                "total_items must be an int or None"
            )

        if total_items is not None and total_items < 0:
            raise ValueError(
                "total_items must not be negative"
            )

        if (
            isinstance(visible_items, bool)
            or not isinstance(visible_items, int)
        ):
            raise TypeError(
                "visible_items must be an integer"
            )

        if visible_items < 0:
            raise ValueError(
                "visible_items must not be negative"
            )

        total = (
            total_items
            if total_items is not None
            else visible_items
        )

        title = str(rich_panel.title or "")

        if navigation_state is None:
            position = (
                "0 / 0"
                if total == 0
                else f"1–{visible_items} / {total}"
            )
        else:
            viewport = navigation_state.viewport_for(
                panel
            )

            start, end = viewport.bounds(total)

            position = (
                "0 / 0"
                if total == 0
                else f"{start + 1}–{end} / {total}"
            )

            is_active = (
                navigation_state.active_panel is panel
            )

            if is_active:
                rich_panel.border_style = "bold bright_yellow"

        if (
            navigation_state is not None
            and navigation_state.active_panel is panel
        ):
            title = (
                f"▶ {title}"
                if title
                else "▶"
            )

        rich_panel.title = (
            f"{title} · {position}"
            if title
            else position
        )
