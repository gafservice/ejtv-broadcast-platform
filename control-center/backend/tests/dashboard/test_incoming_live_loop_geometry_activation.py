"""Contract for INCOMING V2 geometry activation in Rich Live."""

from unittest.mock import Mock, call, patch

import pytest

from app.dashboard.application import DashboardApplication
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)


class FakeLive:
    def __init__(self, dimensions):
        self.dimensions = iter(dimensions)
        self.update = Mock()
        self.console = Mock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def make_application(view):
    application = Mock(spec=DashboardApplication)

    application._terminal_navigation_state = (
        TerminalNavigationState(active_view=view)
    )

    application.run_once.return_value = Mock()

    return application


def execute_live(application, dimensions):
    live = FakeLive(dimensions)

    live.console.size = next(live.dimensions)

    with (
        patch(
            "app.dashboard.application.Live",
            return_value=live,
        ),
        patch(
            "app.dashboard.application.sleep",
        ),
    ):
        DashboardApplication.run(
            application,
            max_iterations=1,
        )

    return live


def test_incoming_receives_real_terminal_height():
    application = make_application(TerminalView.INCOMING)

    dimensions = [
        Mock(width=122, height=30),
    ]

    live = execute_live(application, dimensions)

    application.run_once.assert_called_once_with(
        terminal_width=122,
        incoming_height=7,
        terminal_height=30,
    )

    assert live.update.call_count == 1


@pytest.mark.parametrize(
    "view",
    (
        TerminalView.GENERAL,
        TerminalView.OUTGOING,
        TerminalView.SYSTEM,
        TerminalView.ALARMS,
        TerminalView.EVENTS,
    ),
)
def test_other_views_preserve_historical_call(view):
    application = make_application(view)

    execute_live(
        application,
        [Mock(width=122, height=30)],
    )

    application.run_once.assert_called_once_with(
        terminal_width=122,
        incoming_height=7,
    )


def test_incoming_small_terminal_receives_actual_height():
    application = make_application(TerminalView.INCOMING)

    execute_live(
        application,
        [Mock(width=90, height=12)],
    )

    application.run_once.assert_called_once_with(
        terminal_width=90,
        incoming_height=1,
        terminal_height=12,
    )
