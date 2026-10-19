"""Integration contract for INCOMING V2 TRANSPORT tab."""

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


def make_dashboard():
    incoming = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="MPEG-TS",
                protocol="UDP",
                status="ACTIVE",
                bitrate_receive_mbps=2.21,
                health_status=HealthStatus.DEGRADED,
                transport_health_status=HealthStatus.HEALTHY,
                remote_address="10.0.18.51:3000",
                health_reason="Media degraded",
            ),
            IncomingRowData(
                path_name="impact",
                source="SRT",
                protocol="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=5.87,
                health_status=HealthStatus.HEALTHY,
                transport_health_status=HealthStatus.CRITICAL,
                remote_address="192.0.2.30:8050",
            ),
        )
    )

    return replace(
        build_dashboard_data(),
        incoming=incoming,
    )


def render_tab(tab, selected_path_name="ejtv"):
    selection = IncomingSelectionState(
        selected_path_name=selected_path_name,
    )

    layout = DashboardRenderer().render(
        make_dashboard(),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=selection,
        incoming_detail_tab_state=IncomingDetailTabState(
            active_tab=tab,
        ),
        incoming_visible_capacity=5,
    )

    detail = layout["incoming"]["signal_detail"].renderable

    return detail, selection


def test_transport_tab_uses_six_card_renderer():
    detail, _ = render_tab(IncomingDetailTab.TRANSPORT)

    assert isinstance(detail, Panel)
    assert detail.title == "TRANSPORT DETAIL"
    assert isinstance(detail.renderable, Table)

    assert len(detail.renderable.rows) == 3


def test_transport_tab_preserves_selected_path():
    detail, selection = render_tab(
        IncomingDetailTab.TRANSPORT,
        "impact",
    )

    assert selection.selected_path_name == "impact"

    assert isinstance(detail.renderable, Table)

    first_row = tuple(detail.renderable.columns[0].cells)[0]

    assert isinstance(first_row, Panel)
    assert first_row.title == "CONNECTION"

    fields = tuple(
        first_row.renderable.columns[1].cells
    )

    assert "impact" in fields
    assert "192.0.2.30:8050" in fields
    assert "10.0.18.51:3000" not in fields


def test_transport_tab_uses_transport_health_not_signal_health():
    detail, _ = render_tab(
        IncomingDetailTab.TRANSPORT,
        "ejtv",
    )

    assert isinstance(detail.renderable, Table)

    health_card = tuple(detail.renderable.columns[1].cells)[2]

    assert isinstance(health_card, Panel)
    assert health_card.title == "TRANSPORT HEALTH"

    values = tuple(
        health_card.renderable.columns[1].cells
    )

    assert "HEALTHY" in values
    assert "DEGRADED" not in values


def test_signal_tab_preserves_existing_renderer():
    detail, _ = render_tab(IncomingDetailTab.SIGNAL)

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

    assert fields["Path"] == "ejtv"
    assert fields["Health Status"] == "DEGRADED"


@pytest.mark.parametrize(
    "tab",
    (
        IncomingDetailTab.VIDEO,
        IncomingDetailTab.AUDIO,
        IncomingDetailTab.EVENTS,
        IncomingDetailTab.STATISTICS,
    ),
)
def test_other_tabs_keep_placeholder(tab):
    detail, _ = render_tab(tab)

    assert isinstance(detail, Panel)
    assert detail.title == f"{tab.name} DETAIL"
    assert "Metrics: N/A" in str(detail.renderable)
