"""Totales disponibles para navegación en paneles dinámicos."""

from __future__ import annotations

from dataclasses import dataclass

from app.dashboard.models.dashboard_navigation_state import (
    NavigablePanel,
)


@dataclass(frozen=True, slots=True)
class DashboardNavigationTotals:
    """Cantidad total de elementos disponibles por panel."""

    active_connections: int = 0
    active_alarms: int = 0
    recent_events: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("active_connections", self.active_connections),
            ("active_alarms", self.active_alarms),
            ("recent_events", self.recent_events),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int")

            if value < 0:
                raise ValueError(
                    f"{name} must be greater than or equal to zero"
                )

    def for_panel(
        self,
        panel: NavigablePanel,
    ) -> int:
        if not isinstance(panel, NavigablePanel):
            raise TypeError("panel must be a NavigablePanel")

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
