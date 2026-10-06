"""Estado de navegación entre vistas del Terminal Dashboard."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class TerminalView(str, Enum):
    """Vistas operacionales de primer nivel del Terminal Dashboard."""

    GENERAL = "general"
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    SYSTEM = "system"
    ALARMS = "alarms"
    EVENTS = "events"


_VIEW_ORDER = tuple(TerminalView)


@dataclass(frozen=True)
class TerminalNavigationState:
    """Selección inmutable de la vista operacional activa."""

    active_view: TerminalView = TerminalView.GENERAL

    def __post_init__(self) -> None:
        if not isinstance(self.active_view, TerminalView):
            raise TypeError("active_view must be a TerminalView")

    def select(self, view: TerminalView) -> "TerminalNavigationState":
        if not isinstance(view, TerminalView):
            raise TypeError("view must be a TerminalView")

        return replace(self, active_view=view)

    def select_next(self) -> "TerminalNavigationState":
        index = _VIEW_ORDER.index(self.active_view)
        next_view = _VIEW_ORDER[(index + 1) % len(_VIEW_ORDER)]
        return self.select(next_view)

    def select_previous(self) -> "TerminalNavigationState":
        index = _VIEW_ORDER.index(self.active_view)
        previous_view = _VIEW_ORDER[(index - 1) % len(_VIEW_ORDER)]
        return self.select(previous_view)
