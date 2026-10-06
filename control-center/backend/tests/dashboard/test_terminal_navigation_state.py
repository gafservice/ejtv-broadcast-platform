"""Contrato de navegación entre vistas del Terminal Dashboard."""

from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)


def test_defaults_to_general_view() -> None:
    state = TerminalNavigationState()

    assert state.active_view is TerminalView.GENERAL


def test_next_view_cycles_through_operational_views() -> None:
    state = TerminalNavigationState()

    expected = (
        TerminalView.INCOMING,
        TerminalView.OUTGOING,
        TerminalView.SYSTEM,
        TerminalView.ALARMS,
        TerminalView.EVENTS,
        TerminalView.GENERAL,
    )

    for view in expected:
        state = state.select_next()
        assert state.active_view is view


def test_previous_view_wraps_from_general_to_events() -> None:
    state = TerminalNavigationState()

    updated = state.select_previous()

    assert updated.active_view is TerminalView.EVENTS


def test_select_changes_active_view() -> None:
    state = TerminalNavigationState()

    updated = state.select(TerminalView.OUTGOING)

    assert updated.active_view is TerminalView.OUTGOING


def test_navigation_is_immutable() -> None:
    state = TerminalNavigationState()

    updated = state.select_next()

    assert state.active_view is TerminalView.GENERAL
    assert updated.active_view is TerminalView.INCOMING
    assert updated is not state


def test_application_routes_view_actions_to_terminal_navigation() -> None:
    from app.dashboard.application import DashboardApplication
    from app.dashboard.models.dashboard_navigation_action import (
        DashboardNavigationAction,
    )
    from app.dashboard.models.dashboard_navigation_state import (
        DashboardNavigationState,
    )
    from app.dashboard.models.dashboard_navigation_totals import (
        DashboardNavigationTotals,
    )
    from app.dashboard.services.dashboard_navigation_controller import (
        DashboardNavigationController,
    )

    application = DashboardApplication.__new__(DashboardApplication)
    application._navigation_state = DashboardNavigationState()
    application._navigation_totals = DashboardNavigationTotals()
    application._navigation_controller = DashboardNavigationController()
    application._terminal_navigation_state = TerminalNavigationState()

    panel_state_before = application.navigation_state

    assert application.terminal_navigation_state.active_view is TerminalView.GENERAL

    application.apply_navigation_action(
        DashboardNavigationAction.NEXT_VIEW
    )

    assert application.terminal_navigation_state.active_view is TerminalView.INCOMING
    assert application.navigation_state == panel_state_before

    application.apply_navigation_action(
        DashboardNavigationAction.PREVIOUS_VIEW
    )

    assert application.terminal_navigation_state.active_view is TerminalView.GENERAL
    assert application.navigation_state == panel_state_before


def test_application_constructor_initializes_general_terminal_view() -> None:
    from unittest.mock import Mock

    from app.dashboard.application import DashboardApplication

    application = DashboardApplication(
        mediamtx_adapter=Mock(),
        session_adapter=Mock(),
        streaming_service=Mock(),
        session_service=Mock(),
        dashboard_service=Mock(),
        dashboard_renderer=Mock(),
        system_service=Mock(),
    )

    assert (
        application.terminal_navigation_state.active_view
        is TerminalView.GENERAL
    )
