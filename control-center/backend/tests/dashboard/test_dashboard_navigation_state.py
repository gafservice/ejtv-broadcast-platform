import pytest

from app.dashboard.models.dashboard_navigation_state import (
    DashboardNavigationState,
    NavigablePanel,
)
from app.dashboard.models.panel_viewport import PanelViewport


def test_defaults() -> None:
    state = DashboardNavigationState()

    assert (
        state.active_panel
        is NavigablePanel.ACTIVE_CONNECTIONS
    )

    assert state.active_connections.page_size == 7
    assert state.active_alarms.page_size == 5
    assert state.recent_events.page_size == 5


def test_viewport_for_each_panel() -> None:
    state = DashboardNavigationState()

    assert (
        state.viewport_for(
            NavigablePanel.ACTIVE_CONNECTIONS
        )
        is state.active_connections
    )

    assert (
        state.viewport_for(
            NavigablePanel.ACTIVE_ALARMS
        )
        is state.active_alarms
    )

    assert (
        state.viewport_for(
            NavigablePanel.RECENT_EVENTS
        )
        is state.recent_events
    )


def test_select_panel() -> None:
    state = DashboardNavigationState()

    updated = state.select(
        NavigablePanel.RECENT_EVENTS
    )

    assert (
        updated.active_panel
        is NavigablePanel.RECENT_EVENTS
    )


def test_select_next_cycles() -> None:
    state = DashboardNavigationState()

    state = state.select_next()

    assert (
        state.active_panel
        is NavigablePanel.ACTIVE_ALARMS
    )

    state = state.select_next()

    assert (
        state.active_panel
        is NavigablePanel.RECENT_EVENTS
    )

    state = state.select_next()

    assert (
        state.active_panel
        is NavigablePanel.ACTIVE_CONNECTIONS
    )


def test_select_previous_cycles() -> None:
    state = DashboardNavigationState()

    state = state.select_previous()

    assert (
        state.active_panel
        is NavigablePanel.RECENT_EVENTS
    )


def test_replace_viewport_changes_only_one_panel() -> None:
    state = DashboardNavigationState()

    original_connections = state.active_connections
    original_events = state.recent_events

    viewport = PanelViewport(
        offset=3,
        page_size=5,
    )

    updated = state.replace_viewport(
        NavigablePanel.ACTIVE_ALARMS,
        viewport,
    )

    assert updated.active_alarms == viewport
    assert (
        updated.active_connections
        == original_connections
    )
    assert (
        updated.recent_events
        == original_events
    )


def test_move_active_changes_only_selected_panel() -> None:
    state = DashboardNavigationState().select(
        NavigablePanel.RECENT_EVENTS
    )

    updated = state.move_active(
        1,
        total_items=12,
    )

    assert updated.recent_events.offset == 1
    assert updated.active_alarms.offset == 0
    assert updated.active_connections.offset == 0


def test_page_down_active() -> None:
    state = DashboardNavigationState().select(
        NavigablePanel.ACTIVE_ALARMS
    )

    updated = state.page_down_active(
        total_items=20,
    )

    assert updated.active_alarms.offset == 5


def test_page_up_active() -> None:
    state = DashboardNavigationState(
        active_alarms=PanelViewport(
            offset=8,
            page_size=5,
        )
    ).select(
        NavigablePanel.ACTIVE_ALARMS
    )

    updated = state.page_up_active(
        total_items=20,
    )

    assert updated.active_alarms.offset == 3


def test_home_active() -> None:
    state = DashboardNavigationState(
        recent_events=PanelViewport(
            offset=8,
            page_size=5,
        )
    ).select(
        NavigablePanel.RECENT_EVENTS
    )

    updated = state.home_active()

    assert updated.recent_events.offset == 0


def test_end_active() -> None:
    state = DashboardNavigationState().select(
        NavigablePanel.ACTIVE_CONNECTIONS
    )

    updated = state.end_active(
        total_items=20,
    )

    assert updated.active_connections.offset == 13


def test_rejects_invalid_panel() -> None:
    state = DashboardNavigationState()

    with pytest.raises(TypeError):
        state.viewport_for("recent_events")  # type: ignore[arg-type]


def test_rejects_invalid_viewport() -> None:
    state = DashboardNavigationState()

    with pytest.raises(TypeError):
        state.replace_viewport(
            NavigablePanel.RECENT_EVENTS,
            "bad",  # type: ignore[arg-type]
        )
