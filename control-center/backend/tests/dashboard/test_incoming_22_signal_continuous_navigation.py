"""Continuous navigation and physical visibility for 22 signals."""

from dataclasses import replace
from unittest.mock import Mock

from rich.console import Console

from app.dashboard.application import DashboardApplication
from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
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
from app.dashboard.renderers.dashboard_renderer import (
    DashboardRenderer,
)
from tests.dashboard.test_dashboard_renderer import (
    build_dashboard_data,
)


PATHS = tuple(
    f"signal-{index:02d}"
    for index in range(1, 23)
)


def test_continuous_navigation_preserves_physical_visibility():
    app = object.__new__(DashboardApplication)

    app._terminal_navigation_state = (
        TerminalNavigationState().select(
            TerminalView.INCOMING
        )
    )

    app._incoming_selection_state = IncomingSelectionState()
    app._incoming_path_names = ()
    app._incoming_viewport = PanelViewport(page_size=4)

    app._navigation_state = Mock()
    app._navigation_totals = Mock()
    app._navigation_controller = Mock()

    app.build_dashboard = Mock()

    app.reconcile_incoming_selection(PATHS)

    incoming = IncomingPanelData(
        rows=tuple(
            IncomingRowData(
                path_name=path,
                source="publisher",
                status="ready",
                bitrate_receive_mbps=6.0,
                health_status=None,
                protocol="SRT",
                remote_address="192.0.2.10:9000",
            )
            for path in PATHS
        )
    )

    data = replace(
        build_dashboard_data(),
        incoming=incoming,
    )

    renderer = DashboardRenderer()

    console = Console(
        width=100,
        height=30,
        force_terminal=False,
        color_system=None,
    )

    def verify(expected_path):
        selected = (
            app.incoming_selection_state.selected_path_name
        )

        assert selected == expected_path

        viewport = app.incoming_viewport
        start, end = viewport.bounds(len(PATHS))

        assert viewport.page_size == 4
        assert selected in PATHS[start:end]

        layout = renderer.render(
            data,
            terminal_navigation_state=app.terminal_navigation_state,
            incoming_selection_state=app.incoming_selection_state,
            incoming_viewport=viewport,
            incoming_presentation_mode="compact",
        )

        with console.capture() as capture:
            console.print(layout, height=30)

        output = capture.get()

        assert "INCOMING SIGNALS" in output
        assert "SIGNAL DETAIL" in output

        incoming_output, detail_output = output.split(
            "SIGNAL DETAIL",
            maxsplit=1,
        )

        assert selected in incoming_output, (
            f"{selected} clipped from INCOMING"
        )

        assert selected in detail_output, (
            f"{selected} missing from SIGNAL DETAIL"
        )

    verify(PATHS[0])

    for index in range(1, len(PATHS)):
        app.apply_navigation_action(
            DashboardNavigationAction.SCROLL_DOWN
        )
        verify(PATHS[index])

    for index in range(len(PATHS) - 2, -1, -1):
        app.apply_navigation_action(
            DashboardNavigationAction.SCROLL_UP
        )
        verify(PATHS[index])

    app.apply_navigation_action(
        DashboardNavigationAction.END
    )
    verify(PATHS[-1])

    app.apply_navigation_action(
        DashboardNavigationAction.HOME
    )
    verify(PATHS[0])

    app.build_dashboard.assert_not_called()
    app._navigation_controller.apply.assert_not_called()

    assert len(incoming.rows) == 22
