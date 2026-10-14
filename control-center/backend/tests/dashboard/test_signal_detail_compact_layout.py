"""Compact INCOMING layout visibility contract."""

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


def test_compact_terminal_preserves_five_incoming_signals():
    """100x30 must retain five visible incoming paths."""

    names = (
        "ejtv",
        "enlace",
        "impact",
        "test-04",
        "test-05",
    )

    incoming = IncomingPanelData(
        rows=tuple(
            IncomingRowData(
                path_name=name,
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=6.0,
                health_status=None,
                protocol="SRT",
                remote_address=f"192.0.2.{index}:9000",
            )
            for index, name in enumerate(names, start=1)
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

    visible_across_windows = set()

    scenarios = (
        ("enlace", 0),
        ("test-05", 1),
    )

    for selected_path, offset in scenarios:
        viewport = PanelViewport(
            offset=offset,
            page_size=4,
        )

        start, end = viewport.bounds(len(names))

        assert selected_path in names[start:end]

        layout = renderer.render(
            data,
            terminal_navigation_state=TerminalNavigationState(
                active_view=TerminalView.INCOMING,
            ),
            incoming_selection_state=IncomingSelectionState(
                selected_path_name=selected_path,
            ),
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

        assert selected_path in incoming_output
        assert selected_path in detail_output

        for name in names[start:end]:
            assert name in incoming_output, (
                f"Incoming path not physically visible: {name}"
            )
            visible_across_windows.add(name)

    assert visible_across_windows == set(names)
    assert len(incoming.rows) == 5
