"""ENG-013C 235E.25 — INCOMING application navigation contract."""

from unittest.mock import Mock

from app.dashboard.application import DashboardApplication
from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
from app.dashboard.models.terminal_navigation_state import (
    TerminalView,
)


def make_application():
    """Build a minimal application shell for navigation-only tests."""

    application = object.__new__(DashboardApplication)

    application._terminal_navigation_state = (
        __import__(
            "app.dashboard.models.terminal_navigation_state",
            fromlist=["TerminalNavigationState"],
        ).TerminalNavigationState()
    )

    application._navigation_state = Mock()
    application._navigation_totals = Mock()
    application._navigation_controller = Mock()

    return application


def select_incoming(application):
    application._terminal_navigation_state = (
        application._terminal_navigation_state.select(
            TerminalView.INCOMING
        )
    )


def test_application_exposes_incoming_selection_state():
    application = make_application()

    assert application.incoming_selection_state.selected_path_name is None


def test_application_reconciles_incoming_paths():
    application = make_application()

    application.reconcile_incoming_selection(
        ("service-a", "service-b")
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == "service-a"
    )


def test_incoming_down_selects_next_path():
    application = make_application()
    select_incoming(application)

    application.reconcile_incoming_selection(
        ("service-a", "service-b", "service-c")
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == "service-b"
    )


def test_incoming_up_selects_previous_path():
    application = make_application()
    select_incoming(application)

    application.reconcile_incoming_selection(
        ("service-a", "service-b", "service-c")
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_UP
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == "service-a"
    )


def test_incoming_home_and_end():
    application = make_application()
    select_incoming(application)

    application.reconcile_incoming_selection(
        ("service-a", "service-b", "service-c")
    )

    application.apply_navigation_action(
        DashboardNavigationAction.END
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == "service-c"
    )

    application.apply_navigation_action(
        DashboardNavigationAction.HOME
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == "service-a"
    )


def test_incoming_navigation_does_not_touch_general_controller():
    application = make_application()
    select_incoming(application)

    application.reconcile_incoming_selection(
        ("service-a", "service-b")
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    application._navigation_controller.apply.assert_not_called()


def test_incoming_selection_survives_view_change():
    application = make_application()
    select_incoming(application)

    application.reconcile_incoming_selection(
        ("service-a", "service-b")
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    application.apply_navigation_action(
        DashboardNavigationAction.NEXT_VIEW
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == "service-b"
    )


def test_incoming_selection_survives_reordered_capture():
    application = make_application()

    application.reconcile_incoming_selection(
        ("service-a", "service-b")
    )

    select_incoming(application)

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    application.reconcile_incoming_selection(
        ("service-b", "service-a")
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == "service-b"
    )


def test_incoming_selection_falls_back_when_path_disappears():
    application = make_application()

    application.reconcile_incoming_selection(
        ("service-a", "service-b")
    )

    select_incoming(application)

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    application.reconcile_incoming_selection(
        ("service-c", "service-a")
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == "service-c"
    )


def test_incoming_navigation_does_not_recapture():
    application = make_application()
    select_incoming(application)

    application.build_dashboard = Mock()

    application.reconcile_incoming_selection(
        ("service-a", "service-b")
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    application.build_dashboard.assert_not_called()


def test_general_navigation_still_uses_existing_controller():
    application = make_application()

    application._navigation_totals.for_panel.return_value = 3
    application._navigation_controller.apply.return_value = (
        application._navigation_state
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    application._navigation_controller.apply.assert_called_once()
