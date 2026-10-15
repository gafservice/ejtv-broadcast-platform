"""Contract tests for INCOMING contextual tab application navigation."""

from unittest.mock import Mock

import pytest

from app.dashboard.application import DashboardApplication
from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
)
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)


def make_application():
    """Create a minimal application shell for navigation tests."""

    application = object.__new__(DashboardApplication)

    application._terminal_navigation_state = TerminalNavigationState()
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


def test_default_detail_tab_is_signal():
    application = make_application()

    assert (
        application.incoming_detail_tab_state.active_tab
        is IncomingDetailTab.SIGNAL
    )


@pytest.mark.parametrize(
    ("action", "expected_tab"),
    (
        (
            DashboardNavigationAction.SELECT_SIGNAL_TAB,
            IncomingDetailTab.SIGNAL,
        ),
        (
            DashboardNavigationAction.SELECT_TRANSPORT_TAB,
            IncomingDetailTab.TRANSPORT,
        ),
        (
            DashboardNavigationAction.SELECT_VIDEO_TAB,
            IncomingDetailTab.VIDEO,
        ),
        (
            DashboardNavigationAction.SELECT_AUDIO_TAB,
            IncomingDetailTab.AUDIO,
        ),
        (
            DashboardNavigationAction.SELECT_EVENTS_TAB,
            IncomingDetailTab.EVENTS,
        ),
        (
            DashboardNavigationAction.SELECT_STATISTICS_TAB,
            IncomingDetailTab.STATISTICS,
        ),
    ),
)
def test_incoming_actions_select_corresponding_tab(
    action,
    expected_tab,
):
    application = make_application()
    select_incoming(application)

    application.apply_navigation_action(action)

    assert (
        application.incoming_detail_tab_state.active_tab
        is expected_tab
    )


def test_changing_tab_preserves_selected_signal():
    application = make_application()
    select_incoming(application)

    application.reconcile_incoming_selection(
        ("ejtv", "enlace", "impact")
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    selected_before = (
        application.incoming_selection_state.selected_path_name
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SELECT_VIDEO_TAB
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == selected_before
        == "enlace"
    )

    assert (
        application.incoming_detail_tab_state.active_tab
        is IncomingDetailTab.VIDEO
    )


def test_changing_signal_preserves_active_tab():
    application = make_application()
    select_incoming(application)

    application.reconcile_incoming_selection(
        ("ejtv", "enlace", "impact")
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SELECT_AUDIO_TAB
    )

    application.apply_navigation_action(
        DashboardNavigationAction.SCROLL_DOWN
    )

    assert (
        application.incoming_selection_state.selected_path_name
        == "enlace"
    )

    assert (
        application.incoming_detail_tab_state.active_tab
        is IncomingDetailTab.AUDIO
    )


def test_tab_action_outside_incoming_does_not_change_tab():
    application = make_application()

    application.apply_navigation_action(
        DashboardNavigationAction.SELECT_VIDEO_TAB
    )

    assert (
        application.incoming_detail_tab_state.active_tab
        is IncomingDetailTab.SIGNAL
    )


def test_tab_survives_terminal_view_change():
    application = make_application()
    select_incoming(application)

    application.apply_navigation_action(
        DashboardNavigationAction.SELECT_STATISTICS_TAB
    )

    application.apply_navigation_action(
        DashboardNavigationAction.NEXT_VIEW
    )

    application.apply_navigation_action(
        DashboardNavigationAction.PREVIOUS_VIEW
    )

    assert (
        application.terminal_navigation_state.active_view
        is TerminalView.INCOMING
    )

    assert (
        application.incoming_detail_tab_state.active_tab
        is IncomingDetailTab.STATISTICS
    )
