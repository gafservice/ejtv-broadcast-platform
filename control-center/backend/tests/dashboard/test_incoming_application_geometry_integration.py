"""INCOMING V2 application geometry integration contract."""

from unittest.mock import Mock

import pytest

from app.dashboard.application import DashboardApplication
from app.dashboard.models.dashboard_models import DashboardData
from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.panel_viewport import PanelViewport
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)


def make_application(*, signal_count: int):
    # Use real application properties and viewport synchronization.
    # Avoid initializing external adapters or network services.
    application = DashboardApplication.__new__(DashboardApplication)

    rows = tuple(
        IncomingRowData(
            path_name=f"signal-{index}",
            source="test",
            status="ready",
            bitrate_receive_mbps=None,
            health_status=None,
        )
        for index in range(signal_count)
    )

    dashboard_data = Mock(spec=DashboardData)
    dashboard_data.incoming = IncomingPanelData(rows=rows)

    application.build_dashboard = Mock(return_value=dashboard_data)
    application._dashboard_renderer = Mock()
    application._dashboard_renderer.render.return_value = Mock()

    application._navigation_state = Mock()
    application._terminal_navigation_state = TerminalNavigationState(
        active_view=TerminalView.INCOMING,
    )

    application._incoming_selection_state = IncomingSelectionState(
        selected_path_name=(
            "signal-0" if signal_count else None
        ),
    )

    application._incoming_path_names = tuple(
        row.path_name for row in rows
    )

    application._incoming_viewport = PanelViewport(
        offset=0,
        page_size=5,
    )

    return application


def execute_v2(application, *, terminal_height):
    DashboardApplication.run_once(
        application,
        terminal_width=122,
        incoming_height=max(1, terminal_height - 23),
        terminal_height=terminal_height,
    )

    return application._dashboard_renderer.render.call_args.kwargs


def test_application_passes_geometry_for_three_signals():
    application = make_application(signal_count=3)

    kwargs = execute_v2(
        application,
        terminal_height=30,
    )

    geometry = kwargs["incoming_vertical_geometry"]

    assert geometry.header_height == 3
    assert geometry.list_height == 6
    assert geometry.detail_height == 21
    assert geometry.visible_rows == 3

    assert kwargs["incoming_visible_capacity"] == 3
    assert kwargs["incoming_viewport"].page_size == 3

    application.build_dashboard.assert_called_once_with()


def test_application_uses_one_capture_for_twenty_signals():
    application = make_application(signal_count=20)

    kwargs = execute_v2(
        application,
        terminal_height=30,
    )

    geometry = kwargs["incoming_vertical_geometry"]

    assert geometry.visible_rows == 8
    assert kwargs["incoming_viewport"].page_size == 8

    application.build_dashboard.assert_called_once_with()


def test_application_preserves_valid_viewport_at_zero_capacity():
    application = make_application(signal_count=20)

    kwargs = execute_v2(
        application,
        terminal_height=12,
    )

    geometry = kwargs["incoming_vertical_geometry"]

    assert geometry.visible_rows == 0
    assert kwargs["incoming_visible_capacity"] == 0

    assert kwargs["incoming_viewport"].page_size > 0

    assert (
        kwargs["incoming_selection_state"].selected_path_name
        == "signal-0"
    )

    application.build_dashboard.assert_called_once_with()


def test_application_handles_missing_incoming_data():
    application = make_application(signal_count=0)

    application.build_dashboard.return_value.incoming = None

    kwargs = execute_v2(
        application,
        terminal_height=30,
    )

    geometry = kwargs["incoming_vertical_geometry"]

    assert geometry.visible_rows == 0
    assert kwargs["incoming_visible_capacity"] == 0

    application.build_dashboard.assert_called_once_with()


def test_application_does_not_activate_v2_without_terminal_height():
    application = make_application(signal_count=3)

    DashboardApplication.run_once(
        application,
        terminal_width=122,
        incoming_height=7,
    )

    kwargs = application._dashboard_renderer.render.call_args.kwargs

    assert "incoming_vertical_geometry" not in kwargs

    application.build_dashboard.assert_called_once_with()


@pytest.mark.parametrize("terminal_height", (0, -1))
def test_application_rejects_invalid_terminal_height(terminal_height):
    application = make_application(signal_count=3)

    with pytest.raises(ValueError):
        DashboardApplication.run_once(
            application,
            terminal_width=122,
            incoming_height=7,
            terminal_height=terminal_height,
        )

    application.build_dashboard.assert_not_called()
