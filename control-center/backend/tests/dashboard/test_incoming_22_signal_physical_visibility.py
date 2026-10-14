"""Physical visibility contract for 22 incoming signals."""

from dataclasses import replace

import pytest
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


PATHS = tuple(
    f"signal-{index:02d}"
    for index in range(1, 23)
)


@pytest.mark.parametrize("selected_index", range(22))
def test_each_of_22_signals_is_physically_visible(
    selected_index,
):
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

    selected_path = PATHS[selected_index]

    selection = IncomingSelectionState(
        selected_path_name=selected_path,
    )

    viewport = selection.ensure_visible(
        PanelViewport(page_size=4),
        PATHS,
    )

    start, end = viewport.bounds(len(PATHS))

    assert selected_path in PATHS[start:end]

    layout = DashboardRenderer().render(
        data,
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=selection,
        incoming_viewport=viewport,
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
        f"{selected_path} clipped from INCOMING "
        f"at viewport offset {viewport.offset}"
    )

    assert selected_path in detail_output, (
        f"{selected_path} missing from SIGNAL DETAIL"
    )

    assert len(incoming.rows) == 22
