"""Contract tests for INCOMING contextual detail tab rendering."""

from dataclasses import replace

import pytest

from rich.panel import Panel
from rich.table import Table

from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
    IncomingDetailTabState,
)
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


def build_incoming_dashboard():
    incoming = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="UDP",
                protocol="UDP",
                status="ACTIVE",
                bitrate_receive_mbps=4.0,
                health_status=HealthStatus.HEALTHY,
                remote_address="192.0.2.10:9000",
            ),
            IncomingRowData(
                path_name="enlace",
                source="UDP",
                protocol="UDP",
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

    return replace(
        build_dashboard_data(),
        incoming=incoming,
    )


def render_incoming(tab, selected_path_name="enlace"):
    renderer = DashboardRenderer()

    return renderer.render(
        build_incoming_dashboard(),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=IncomingSelectionState(
            selected_path_name=selected_path_name,
        ),
        incoming_detail_tab_state=IncomingDetailTabState(
            active_tab=tab,
        ),
        incoming_visible_capacity=5,
    )


@pytest.mark.parametrize(
    "tab",
    tuple(IncomingDetailTab),
)
def test_all_six_tabs_are_renderable(tab):
    layout = render_incoming(tab)

    detail = layout["incoming"]["signal_detail"].renderable

    assert isinstance(detail, Panel)
    assert tab.name in detail.title


def test_signal_tab_reuses_existing_signal_detail():
    layout = render_incoming(IncomingDetailTab.SIGNAL)

    detail = layout["incoming"]["signal_detail"].renderable

    assert isinstance(detail, Panel)
    assert isinstance(detail.renderable, Table)

    fields = dict(
        zip(
            *(
                tuple(column.cells)
                for column in detail.renderable.columns
            )
        )
    )

    assert fields["Path"] == "enlace"
    assert fields["Health Status"] == "DEGRADED"
    assert fields["Summary"] == "2 MAJOR"

    assert "192.0.2.10:9000" not in fields.values()


@pytest.mark.parametrize(
    "tab",
    (
        IncomingDetailTab.VIDEO,
        IncomingDetailTab.AUDIO,
        IncomingDetailTab.EVENTS,
        IncomingDetailTab.STATISTICS,
    ),
)
def test_specialized_tabs_show_explicit_unavailable_state(tab):
    layout = render_incoming(tab)

    detail = layout["incoming"]["signal_detail"].renderable

    assert isinstance(detail, Panel)
    assert "N/A" in str(detail.renderable)


def test_rendering_does_not_mutate_selected_signal():
    selection = IncomingSelectionState(
        selected_path_name="enlace",
    )

    renderer = DashboardRenderer()

    renderer.render(
        build_incoming_dashboard(),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=selection,
        incoming_detail_tab_state=IncomingDetailTabState(
            active_tab=IncomingDetailTab.VIDEO,
        ),
        incoming_visible_capacity=5,
    )

    assert selection.selected_path_name == "enlace"
