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

        b"\x1b[C": DashboardNavigationAction.NEXT_VIEW,
        b"\x1b[D": DashboardNavigationAction.PREVIOUS_VIEW,

        b"\x1bOA": DashboardNavigationAction.SCROLL_UP,
        b"\x1bOB": DashboardNavigationAction.SCROLL_DOWN,
        b"\x1bOC": DashboardNavigationAction.NEXT_VIEW,
        b"\x1bOD": DashboardNavigationAction.PREVIOUS_VIEW,

        b"\x1b[5~": DashboardNavigationAction.PAGE_UP,
        b"\x1b[6~": DashboardNavigationAction.PAGE_DOWN,

        b"\x1b[H": DashboardNavigationAction.HOME,
        b"\x1b[F": DashboardNavigationAction.END,

        b"1": DashboardNavigationAction.SELECT_SIGNAL_TAB,
        b"2": DashboardNavigationAction.SELECT_TRANSPORT_TAB,
        b"3": DashboardNavigationAction.SELECT_VIDEO_TAB,
        b"4": DashboardNavigationAction.SELECT_AUDIO_TAB,
        b"5": DashboardNavigationAction.SELECT_EVENTS_TAB,
        b"6": DashboardNavigationAction.SELECT_STATISTICS_TAB,

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
