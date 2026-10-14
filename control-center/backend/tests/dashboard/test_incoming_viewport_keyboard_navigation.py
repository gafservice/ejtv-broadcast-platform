"""Contract tests for INCOMING keyboard viewport synchronization."""

from unittest.mock import Mock

from app.dashboard.application import DashboardApplication
from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.panel_viewport import PanelViewport
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)


PATHS = (
    "ejtv",
    "enlace",
    "impact",
    "test-04",
    "test-05",
    "test-06",
    "test-07",
)


def make_application():
    app = object.__new__(DashboardApplication)

    app._terminal_navigation_state = (
        TerminalNavigationState().select(TerminalView.INCOMING)
    )

    app._incoming_selection_state = IncomingSelectionState()
    app._incoming_path_names = ()
    app._incoming_viewport = PanelViewport(page_size=3)

    app._navigation_state = Mock()
    app._navigation_totals = Mock()
    app._navigation_controller = Mock()

    app.reconcile_incoming_selection(PATHS)

    return app


def assert_selection_visible(app):
    selected = app.incoming_selection_state.selected_path_name
    start, end = app.incoming_viewport.bounds(len(PATHS))

    assert selected in PATHS
    assert start <= PATHS.index(selected) < end


def test_scroll_down_moves_viewport_when_selection_exits_window():
    app = make_application()

    for _ in range(3):
        app.apply_navigation_action(
            DashboardNavigationAction.SCROLL_DOWN
        )

    assert app.incoming_selection_state.selected_path_name == "test-04"
    assert app.incoming_viewport.offset == 1
    assert_selection_visible(app)


def test_scroll_up_moves_viewport_when_selection_exits_window():
    app = make_application()

    app._incoming_selection_state = IncomingSelectionState(
        selected_path_name="test-05",
    )
    app.synchronize_incoming_viewport()

    assert app.incoming_viewport.offset == 2

    for _ in range(3):
        app.apply_navigation_action(
            DashboardNavigationAction.SCROLL_UP
        )

    assert app.incoming_selection_state.selected_path_name == "enlace"
    assert app.incoming_viewport.offset == 1
    assert_selection_visible(app)


def test_home_moves_selection_and_viewport_to_start():
    app = make_application()

    app._incoming_selection_state = IncomingSelectionState(
        selected_path_name="test-07",
    )
    app.synchronize_incoming_viewport()

    app.apply_navigation_action(
        DashboardNavigationAction.HOME
    )

    assert app.incoming_selection_state.selected_path_name == "ejtv"
    assert app.incoming_viewport.offset == 0
    assert_selection_visible(app)


def test_end_moves_selection_and_viewport_to_last_window():
    app = make_application()

    app.apply_navigation_action(
        DashboardNavigationAction.END
    )

    assert app.incoming_selection_state.selected_path_name == "test-07"
    assert app.incoming_viewport.offset == 4
    assert_selection_visible(app)


def test_incoming_keyboard_does_not_use_general_navigation_or_capture():
    app = make_application()
    app.build_dashboard = Mock()

    app.apply_navigation_action(
        DashboardNavigationAction.END
    )

    app._navigation_controller.apply.assert_not_called()
    app.build_dashboard.assert_not_called()
    assert_selection_visible(app)
