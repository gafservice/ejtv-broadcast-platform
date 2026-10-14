"""Same-session resize contract for INCOMING."""

from dataclasses import replace
from unittest.mock import Mock

from rich.console import Console

from app.dashboard.application import DashboardApplication
from app.dashboard.models.dashboard_navigation_state import DashboardNavigationState
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


def test_selected_identity_survives_same_session_resize():
    app = object.__new__(DashboardApplication)

    app._terminal_navigation_state = (
        TerminalNavigationState().select(
            TerminalView.INCOMING
        )
    )

    app._incoming_selection_state = IncomingSelectionState(
        selected_path_name="signal-18"
    )

    app._incoming_path_names = ()
    app._incoming_viewport = PanelViewport(page_size=5)

    app._navigation_state = DashboardNavigationState()
    app._navigation_totals = Mock()
    app._navigation_controller = Mock()

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

    capture_calls = 0

    def fake_build_dashboard():
        nonlocal capture_calls

        capture_calls += 1
        app.reconcile_incoming_selection(PATHS)

        return data

    app.build_dashboard = fake_build_dashboard
    app._dashboard_renderer = DashboardRenderer()

    scenarios = (
        (100, 30, 7, 4),
        (120, 40, 17, 14),
        (160, 50, 27, 24),
        (100, 30, 7, 4),
    )

    for width, height, incoming_height, expected_page_size in scenarios:
        layout = app.run_once(
            terminal_width=width,
            incoming_height=incoming_height,
        )

        assert (
            app.incoming_selection_state.selected_path_name
            == "signal-18"
        )

        viewport = app.incoming_viewport

        assert viewport.page_size == expected_page_size

        start, end = viewport.bounds(len(PATHS))

        assert "signal-18" in PATHS[start:end]

        console = Console(
            width=width,
            height=height,
            force_terminal=False,
            color_system=None,
        )

        with console.capture() as capture:
            console.print(layout, height=height)

        output = capture.get()

        assert "INCOMING SIGNALS" in output
        assert "SIGNAL DETAIL" in output

        incoming_output, detail_output = output.split(
            "SIGNAL DETAIL",
            maxsplit=1,
        )

        assert "signal-18" in incoming_output, (
            f"Selection clipped at {width}x{height}"
        )

        assert "signal-18" in detail_output, (
            f"Signal Detail mismatch at {width}x{height}"
        )

        assert len(incoming.rows) == 22

    assert capture_calls == len(scenarios)
    app._navigation_controller.apply.assert_not_called()
