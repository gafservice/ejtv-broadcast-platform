"""Acciones de navegación interactiva del dashboard."""

from __future__ import annotations

from enum import Enum


class DashboardNavigationAction(str, Enum):
    """Acciones abstractas producidas por la entrada del usuario."""

    NEXT_PANEL = "next_panel"
    PREVIOUS_PANEL = "previous_panel"

    NEXT_VIEW = "next_view"
    PREVIOUS_VIEW = "previous_view"

    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"

    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"

    HOME = "home"
    END = "end"

    SELECT_SIGNAL_TAB = "select_signal_tab"
    SELECT_TRANSPORT_TAB = "select_transport_tab"
    SELECT_VIDEO_TAB = "select_video_tab"
    SELECT_AUDIO_TAB = "select_audio_tab"
    SELECT_EVENTS_TAB = "select_events_tab"
    SELECT_STATISTICS_TAB = "select_statistics_tab"

    QUIT = "quit"
