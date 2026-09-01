"""Acciones de navegación interactiva del dashboard."""

from __future__ import annotations

from enum import Enum


class DashboardNavigationAction(str, Enum):
    """Acciones abstractas producidas por la entrada del usuario."""

    NEXT_PANEL = "next_panel"
    PREVIOUS_PANEL = "previous_panel"

    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"

    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"

    HOME = "home"
    END = "end"

    QUIT = "quit"
