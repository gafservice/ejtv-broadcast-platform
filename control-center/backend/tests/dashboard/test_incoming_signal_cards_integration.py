"""INCOMING V2 SIGNAL cards integration contract."""

from unittest.mock import Mock

import pytest
from rich.console import Console, Group
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
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.services.incoming_vertical_geometry_policy import (
    IncomingVerticalGeometryPolicy,
)
from app.domain.streaming.health import HealthStatus


def make_incoming():
    return IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=2.21,
                health_status=HealthStatus.HEALTHY,
                protocol="UDP",
                remote_address="10.0.18.51:3000",
                alarm_count=0,
            ),
            IncomingRowData(
                path_name="impact",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=5.87,
                health_status=HealthStatus.CRITICAL,
                protocol="SRT",
                remote_address="192.0.2.30:8050",
                alarm_count=2,
                alarm_severity="MAJOR",
            ),
        )
    )


def render_detail(
    *,
    terminal_height=30,
    use_geometry=True,
    tab=IncomingDetailTab.SIGNAL,
    selected="ejtv",
):
    renderer = DashboardRenderer()

    renderer._incoming_panel_renderer = Mock()
    renderer._incoming_panel_renderer.render.return_value = Panel(
        "INCOMING LIST",
        title="INCOMING SIGNALS",
    )

    renderer._signal_detail_renderer = Mock()
    renderer._signal_detail_renderer.render.return_value = Panel(
        "HISTORICAL DETAIL",
        title="SIGNAL DETAIL",
    )

    incoming = make_incoming()
    geometry = (
        IncomingVerticalGeometryPolicy().calculate(
            terminal_height=terminal_height,
            signal_count=len(incoming.rows),
            maximum_visible_rows=8,
        )
        if use_geometry
        else None
    )

    data = Mock()
    data.incoming = incoming

    layout = renderer.render(
        data,
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=IncomingSelectionState(
            selected_path_name=selected,
        ),
        incoming_detail_tab_state=IncomingDetailTabState(
            active_tab=tab,
        ),
        incoming_visible_capacity=(
            geometry.visible_rows if geometry is not None else 5
        ),
        incoming_vertical_geometry=geometry,
        terminal_width=122,
    )

    panel = layout["incoming"]["signal_detail"].renderable

    console = Console(
        width=122,
        force_terminal=False,
        color_system=None,
    )
    with console.capture() as capture:
        console.print(panel)

    return panel, capture.get(), renderer


def test_v2_signal_uses_four_cards():
    _, screen, renderer = render_detail()

    for title in (
        "IDENTIFICACIÓN",
        "RECEPCIÓN",
        "HEALTH",
        "ALARMAS",
    ):
        assert title in screen

    assert "2.21 Mbps" in screen
    assert "10.0.18.51:3000" in screen
    renderer._signal_detail_renderer.render.assert_not_called()


def test_v2_cards_follow_selected_signal():
    _, screen, renderer = render_detail(selected="impact")

    assert "5.87 Mbps" in screen
    assert "192.0.2.30:8050" in screen
    assert "MAJOR" in screen
    assert "10.0.18.51:3000" not in screen
    renderer._signal_detail_renderer.render.assert_not_called()


def test_v2_missing_selection_does_not_substitute_signal():
    _, screen, renderer = render_detail(selected=None)

    assert "No incoming signal selected." in screen
    assert "10.0.18.51:3000" not in screen
    renderer._signal_detail_renderer.render.assert_not_called()


def test_historical_path_remains_unchanged():
    panel, _, renderer = render_detail(use_geometry=False)

    assert panel.renderable == "HISTORICAL DETAIL"
    renderer._signal_detail_renderer.render.assert_called_once()


@pytest.mark.parametrize("terminal_height", (12, 20, 24))
def test_small_terminal_uses_historical_detail(terminal_height):
    panel, _, renderer = render_detail(
        terminal_height=terminal_height,
    )

    assert isinstance(panel.renderable, Group)
    assert any(
        item == "HISTORICAL DETAIL"
        for item in panel.renderable.renderables
    )
    renderer._signal_detail_renderer.render.assert_called_once()


@pytest.mark.parametrize(
    "tab",
    (
        IncomingDetailTab.TRANSPORT,
        IncomingDetailTab.VIDEO,
        IncomingDetailTab.AUDIO,
        IncomingDetailTab.EVENTS,
        IncomingDetailTab.STATISTICS,
    ),
)
def test_other_tabs_do_not_activate_signal_cards(tab):
    panel, _, renderer = render_detail(tab=tab)

    assert isinstance(panel.renderable, Group)
    if tab is IncomingDetailTab.TRANSPORT:
        assert any(
            isinstance(item, Table)
            for item in panel.renderable.renderables
        )
    else:
        assert any(
            isinstance(item, str) and "Metrics: N/A" in item
            for item in panel.renderable.renderables
        )
    renderer._signal_detail_renderer.render.assert_not_called()
