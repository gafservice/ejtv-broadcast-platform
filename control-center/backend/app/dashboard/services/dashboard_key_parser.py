"""Traducción de secuencias de teclado a acciones del dashboard."""

from __future__ import annotations

from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)


class DashboardKeyParser:
    """Convierte secuencias ANSI del terminal en acciones abstractas."""

    _SEQUENCES = {
        b"\t": DashboardNavigationAction.NEXT_PANEL,
        b"\x1b[Z": DashboardNavigationAction.PREVIOUS_PANEL,

        b"\x1b[A": DashboardNavigationAction.SCROLL_UP,
        b"\x1b[B": DashboardNavigationAction.SCROLL_DOWN,

        b"\x1b[5~": DashboardNavigationAction.PAGE_UP,
        b"\x1b[6~": DashboardNavigationAction.PAGE_DOWN,

        b"\x1b[H": DashboardNavigationAction.HOME,
        b"\x1b[F": DashboardNavigationAction.END,

        b"q": DashboardNavigationAction.QUIT,
        b"Q": DashboardNavigationAction.QUIT,
    }

    def parse(
        self,
        sequence: bytes,
    ) -> DashboardNavigationAction | None:
        """Devuelve la acción asociada o None si no se reconoce."""

        if not isinstance(sequence, bytes):
            raise TypeError("sequence must be bytes")

        return self._SEQUENCES.get(sequence)
