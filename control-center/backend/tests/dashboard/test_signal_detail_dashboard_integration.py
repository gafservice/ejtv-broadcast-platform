"""Contract tests for contextual Signal Detail integration."""

from dataclasses import replace

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)
from app.dashboard.renderers.dashboard_renderer import (
    DashboardRenderer,
)
from app.domain.streaming.health import HealthStatus

from tests.dashboard.test_dashboard_renderer import (
    build_dashboard_data,
)


def test_incoming_layout_contains_selected_signal_detail():
    """INCOMING must contain list and contextual detail."""

    incoming = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=4.0,
                health_status=HealthStatus.HEALTHY,
                remote_address="192.0.2.10:9000",
            ),
            IncomingRowData(
                path_name="enlace",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=6.0,
                health_status=HealthStatus.DEGRADED,
                remote_address="192.0.2.20:9000",
                health_reason="Packet loss detected",
                alarm_count=2,
                alarm_severity="MAJOR",
            ),
        )
    )

    data = replace(
        build_dashboard_data(),
        incoming=incoming,
    )

    terminal = TerminalNavigationState(
        active_view=TerminalView.INCOMING,
    )

    selection = IncomingSelectionState(
        selected_path_name="enlace",
    )

    layout = DashboardRenderer().render(
        data,
        terminal_navigation_state=terminal,
        incoming_selection_state=selection,
    )

    assert isinstance(layout, Layout)

    incoming_layout = layout["incoming"]

    list_layout = incoming_layout["incoming_list"]
    detail_layout = incoming_layout["signal_detail"]

    assert isinstance(list_layout.renderable, Panel)
    assert isinstance(detail_layout.renderable, Panel)

    assert isinstance(
        list_layout.renderable.renderable,
        Table,
    )

    assert isinstance(
        detail_layout.renderable.renderable,
        Table,
    )

    detail_table = detail_layout.renderable.renderable

    fields = dict(
        zip(
            *(
                tuple(column.cells)
                for column in detail_table.columns
            )
        )
    )

    assert fields["Path"] == "enlace"
    assert fields["Remote"] == "192.0.2.20:9000"
    assert fields["Health Status"] == "DEGRADED"
    assert fields["Summary"] == "2 MAJOR"

    assert "192.0.2.10:9000" not in fields.values()
