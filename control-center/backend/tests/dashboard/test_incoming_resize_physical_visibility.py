"""Physical visibility across terminal dimensions."""

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
from app.dashboard.services.incoming_presentation_policy import (
    IncomingPresentationPolicy,
)
from tests.dashboard.test_dashboard_renderer import (
    build_dashboard_data,
)


PATHS = tuple(
    f"signal-{index:02d}"
    for index in range(1, 23)
)


@pytest.mark.parametrize(
    "width,height,incoming_height,selected_index",
    [
        (100, 30, 7, 0),
        (100, 30, 7, 10),
        (100, 30, 7, 21),
        (120, 40, 17, 0),
        (120, 40, 17, 10),
        (120, 40, 17, 21),
        (160, 50, 27, 0),
        (160, 50, 27, 10),
        (160, 50, 27, 21),
    ],
)
def test_selected_signal_survives_physical_resize(
    width,
    height,
    incoming_height,
    selected_index,
):
    presentation = IncomingPresentationPolicy().calculate(
        terminal_width=width,
        incoming_height=incoming_height,
    )

    assert presentation.page_size > 0

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
        PanelViewport(
            page_size=presentation.page_size,
        ),
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
        incoming_presentation_mode=presentation.mode,
    )

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

    assert selected_path in incoming_output, (
        f"{selected_path} clipped from INCOMING "
        f"at {width}x{height}, mode={presentation.mode}, "
        f"page_size={presentation.page_size}"
    )

    assert selected_path in detail_output, (
        f"{selected_path} missing from SIGNAL DETAIL "
        f"at {width}x{height}"
    )

    assert len(incoming.rows) == 22
