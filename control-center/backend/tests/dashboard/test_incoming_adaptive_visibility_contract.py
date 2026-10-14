"""Physical visibility contract for adaptive INCOMING."""

from dataclasses import replace

from rich.console import Console

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


def test_selected_incoming_path_is_physically_visible_at_100x30():
    """The selected path must appear in both physical panels."""

    paths = (
        "ejtv",
        "enlace",
        "impact",
        "test-04",
        "test-05",
        "test-06",
        "test-07",
    )

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
            for path in paths
        )
    )

    data = replace(
        build_dashboard_data(),
        incoming=incoming,
    )

    selected_path = "test-05"

    layout = DashboardRenderer().render(
        data,
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=IncomingSelectionState(
            selected_path_name=selected_path,
        ),
        incoming_viewport=PanelViewport(
            offset=2,
            page_size=4,
        ),
        incoming_presentation_mode="compact",
    )

    console = Console(
        width=100,
        height=30,
        force_terminal=False,
        color_system=None,
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

    assert selected_path in incoming_output, (
        "Selected signal is logically inside the viewport "
        "but physically clipped from INCOMING."
    )

    assert selected_path in detail_output
    assert len(incoming.rows) == 7
