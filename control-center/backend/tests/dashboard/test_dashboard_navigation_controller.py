"""Pruebas del controlador de navegación del dashboard."""

import pytest

from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
from app.dashboard.models.dashboard_navigation_state import (
    DashboardNavigationState,
    NavigablePanel,
)
from app.dashboard.models.panel_viewport import PanelViewport
from app.dashboard.services.dashboard_navigation_controller import (
    DashboardNavigationController,
)


def test_next_panel_changes_only_selection() -> None:
    controller = DashboardNavigationController()
    state = DashboardNavigationState()

    updated = controller.apply(
        state,
        DashboardNavigationAction.NEXT_PANEL,
        total_items=20,
    )

    assert updated.active_panel is NavigablePanel.ACTIVE_ALARMS
    assert updated.active_connections == state.active_connections
    assert updated.active_alarms == state.active_alarms
    assert updated.recent_events == state.recent_events


def test_previous_panel_changes_only_selection() -> None:
    controller = DashboardNavigationController()
    state = DashboardNavigationState()

    updated = controller.apply(
        state,
        DashboardNavigationAction.PREVIOUS_PANEL,
        total_items=20,
    )

    assert updated.active_panel is NavigablePanel.RECENT_EVENTS


def test_scroll_down_moves_only_active_panel() -> None:
    controller = DashboardNavigationController()

    state = DashboardNavigationState(
        active_connections=PanelViewport(
            offset=4,
            page_size=7,
        ),
        active_alarms=PanelViewport(
            offset=8,
            page_size=5,
        ),
        recent_events=PanelViewport(
            offset=12,
            page_size=5,
        ),
    )

    updated = controller.apply(
        state,
        DashboardNavigationAction.SCROLL_DOWN,
        total_items=30,
    )

    assert updated.active_connections == PanelViewport(
        offset=5,
        page_size=7,
    )
    assert updated.active_alarms == state.active_alarms
    assert updated.recent_events == state.recent_events


def test_scroll_up_clamps_at_zero() -> None:
    controller = DashboardNavigationController()
    state = DashboardNavigationState()

    updated = controller.apply(
        state,
        DashboardNavigationAction.SCROLL_UP,
        total_items=20,
    )

    assert updated.active_connections.offset == 0


def test_page_down_moves_one_page() -> None:
    controller = DashboardNavigationController()
    state = DashboardNavigationState()

    updated = controller.apply(
        state,
        DashboardNavigationAction.PAGE_DOWN,
        total_items=30,
    )

    assert updated.active_connections.offset == 7


def test_page_up_moves_one_page() -> None:
    controller = DashboardNavigationController()

    state = DashboardNavigationState(
        active_connections=PanelViewport(
            offset=14,
            page_size=7,
        ),
    )

    updated = controller.apply(
        state,
        DashboardNavigationAction.PAGE_UP,
        total_items=30,
    )

    assert updated.active_connections.offset == 7


def test_home_moves_active_panel_to_zero() -> None:
    controller = DashboardNavigationController()

    state = DashboardNavigationState(
        active_connections=PanelViewport(
            offset=9,
            page_size=7,
        ),
    )

    updated = controller.apply(
        state,
        DashboardNavigationAction.HOME,
        total_items=30,
    )

    assert updated.active_connections.offset == 0


def test_end_moves_active_panel_to_last_window() -> None:
    controller = DashboardNavigationController()
    state = DashboardNavigationState()

    updated = controller.apply(
        state,
        DashboardNavigationAction.END,
        total_items=20,
    )

    assert updated.active_connections == PanelViewport(
        offset=13,
        page_size=7,
    )


def test_selected_alarm_panel_moves_independently() -> None:
    controller = DashboardNavigationController()

    state = DashboardNavigationState(
        active_panel=NavigablePanel.ACTIVE_ALARMS,
        active_connections=PanelViewport(
            offset=4,
            page_size=7,
        ),
        active_alarms=PanelViewport(
            offset=8,
            page_size=5,
        ),
        recent_events=PanelViewport(
            offset=12,
            page_size=5,
        ),
    )

    updated = controller.apply(
        state,
        DashboardNavigationAction.SCROLL_DOWN,
        total_items=30,
    )

    assert updated.active_connections.offset == 4
    assert updated.active_alarms.offset == 9
    assert updated.recent_events.offset == 12


def test_quit_does_not_modify_navigation_state() -> None:
    controller = DashboardNavigationController()
    state = DashboardNavigationState()

    updated = controller.apply(
        state,
        DashboardNavigationAction.QUIT,
        total_items=20,
    )

    assert updated == state


@pytest.mark.parametrize(
    "invalid_state",
    (
        None,
        object(),
        "state",
    ),
)
def test_rejects_invalid_state(
    invalid_state,
) -> None:
    controller = DashboardNavigationController()

    with pytest.raises(
        TypeError,
        match="state must be a DashboardNavigationState",
    ):
        controller.apply(
            invalid_state,
            DashboardNavigationAction.HOME,
            total_items=10,
        )


@pytest.mark.parametrize(
    "invalid_action",
    (
        None,
        "scroll_down",
        object(),
    ),
)
def test_rejects_invalid_action(
    invalid_action,
) -> None:
    controller = DashboardNavigationController()

    with pytest.raises(
        TypeError,
        match="action must be a DashboardNavigationAction",
    ):
        controller.apply(
            DashboardNavigationState(),
            invalid_action,
            total_items=10,
        )
