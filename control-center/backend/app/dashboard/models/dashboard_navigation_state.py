"""Estado de navegación interactiva del dashboard."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from app.dashboard.models.panel_viewport import PanelViewport


class NavigablePanel(str, Enum):
    """Paneles del dashboard que admiten navegación."""

    ACTIVE_CONNECTIONS = "active_connections"
    ACTIVE_ALARMS = "active_alarms"
    RECENT_EVENTS = "recent_events"


@dataclass(frozen=True, slots=True)
class DashboardNavigationState:
    """Mantiene selección y viewport independiente por panel."""

    active_panel: NavigablePanel = NavigablePanel.ACTIVE_CONNECTIONS

    active_connections: PanelViewport = PanelViewport(
        page_size=7,
    )

    active_alarms: PanelViewport = PanelViewport(
        page_size=5,
    )

    recent_events: PanelViewport = PanelViewport(
        page_size=5,
    )

    def viewport_for(
        self,
        panel: NavigablePanel,
    ) -> PanelViewport:
        """Obtiene el viewport asociado al panel solicitado."""

        if not isinstance(panel, NavigablePanel):
            raise TypeError(
                "panel must be a NavigablePanel"
            )

        mapping = {
            NavigablePanel.ACTIVE_CONNECTIONS: (
                self.active_connections
            ),
            NavigablePanel.ACTIVE_ALARMS: (
                self.active_alarms
            ),
            NavigablePanel.RECENT_EVENTS: (
                self.recent_events
            ),
        }

        return mapping[panel]

    def select(
        self,
        panel: NavigablePanel,
    ) -> "DashboardNavigationState":
        """Selecciona explícitamente un panel."""

        if not isinstance(panel, NavigablePanel):
            raise TypeError(
                "panel must be a NavigablePanel"
            )

        return replace(
            self,
            active_panel=panel,
        )

    def select_next(
        self,
    ) -> "DashboardNavigationState":
        """Avanza al siguiente panel navegable."""

        order = tuple(NavigablePanel)

        index = order.index(self.active_panel)

        return replace(
            self,
            active_panel=order[
                (index + 1) % len(order)
            ],
        )

    def select_previous(
        self,
    ) -> "DashboardNavigationState":
        """Retrocede al panel navegable anterior."""

        order = tuple(NavigablePanel)

        index = order.index(self.active_panel)

        return replace(
            self,
            active_panel=order[
                (index - 1) % len(order)
            ],
        )

    def replace_viewport(
        self,
        panel: NavigablePanel,
        viewport: PanelViewport,
    ) -> "DashboardNavigationState":
        """Reemplaza únicamente el viewport indicado."""

        if not isinstance(panel, NavigablePanel):
            raise TypeError(
                "panel must be a NavigablePanel"
            )

        if not isinstance(viewport, PanelViewport):
            raise TypeError(
                "viewport must be a PanelViewport"
            )

        field_names = {
            NavigablePanel.ACTIVE_CONNECTIONS: (
                "active_connections"
            ),
            NavigablePanel.ACTIVE_ALARMS: (
                "active_alarms"
            ),
            NavigablePanel.RECENT_EVENTS: (
                "recent_events"
            ),
        }

        return replace(
            self,
            **{
                field_names[panel]: viewport,
            },
        )

    def move_active(
        self,
        delta: int,
        *,
        total_items: int,
    ) -> "DashboardNavigationState":
        """Desplaza el viewport del panel seleccionado."""

        current = self.viewport_for(
            self.active_panel
        )

        updated = current.move(
            delta,
            total_items=total_items,
        )

        return self.replace_viewport(
            self.active_panel,
            updated,
        )

    def page_up_active(
        self,
        *,
        total_items: int,
    ) -> "DashboardNavigationState":
        """Retrocede una página en el panel activo."""

        current = self.viewport_for(
            self.active_panel
        )

        return self.replace_viewport(
            self.active_panel,
            current.page_up(
                total_items=total_items,
            ),
        )

    def page_down_active(
        self,
        *,
        total_items: int,
    ) -> "DashboardNavigationState":
        """Avanza una página en el panel activo."""

        current = self.viewport_for(
            self.active_panel
        )

        return self.replace_viewport(
            self.active_panel,
            current.page_down(
                total_items=total_items,
            ),
        )

    def home_active(
        self,
    ) -> "DashboardNavigationState":
        """Mueve el panel activo al inicio."""

        current = self.viewport_for(
            self.active_panel
        )

        return self.replace_viewport(
            self.active_panel,
            current.home(),
        )

    def end_active(
        self,
        *,
        total_items: int,
    ) -> "DashboardNavigationState":
        """Mueve el panel activo al final."""

        current = self.viewport_for(
            self.active_panel
        )

        return self.replace_viewport(
            self.active_panel,
            current.end(
                total_items=total_items,
            ),
        )
