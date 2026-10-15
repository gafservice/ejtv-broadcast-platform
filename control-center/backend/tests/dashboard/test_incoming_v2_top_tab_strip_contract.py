"""Contract for top-positioned INCOMING V2 detail tabs."""

from io import StringIO

import pytest
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

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
                source="UDP",
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
    tab=IncomingDetailTab.SIGNAL,
    selected="impact",
    terminal_height=30,
    use_geometry=True,
):
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

    from unittest.mock import Mock

    data = Mock()
    data.incoming = incoming

    renderer = DashboardRenderer()

    renderer._incoming_panel_renderer = Mock()
    renderer._incoming_panel_renderer.render.return_value = Panel(
        "INCOMING LIST",
        title="INCOMING SIGNALS",
    )

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

    output = StringIO()

    console = Console(
        file=output,
        width=122,
        force_terminal=False,
        color_system=None,
    )

    console.print(
        panel,
        height=geometry.detail_height if geometry is not None else 20,
    )

    return panel, output.getvalue()


def test_v2_signal_has_top_tabs_before_cards():
    panel, screen = render_detail()

    assert isinstance(panel, Panel)
    assert isinstance(panel.renderable, Group)
    assert panel.subtitle is None

    tabs_at = screen.index("1 SIGNAL")
    cards_at = screen.index("IDENTIFICACIÓN")

    assert tabs_at < cards_at

    for label in (
        "TRANSPORT",
        "VIDEO",
        "AUDIO",
        "EVENTS",
        "STATS",
        "RECEPCIÓN",
        "HEALTH",
        "ALARMAS",
    ):
        assert label in screen


def test_v2_preserves_signal_header_and_selected_evidence():
    panel, screen = render_detail()

    assert isinstance(panel.title, Text)
    assert "SIGNAL DETAIL" in panel.title.plain
    assert "impact" in panel.title.plain
    assert "CRITICAL" in panel.title.plain

    assert "5.87 Mbps" in screen
    assert "2 MAJOR" in screen
    assert "10.0.18.51:3000" not in screen


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
def test_v2_specialized_tabs_are_top_positioned(tab):
    panel, screen = render_detail(tab=tab)

    assert isinstance(panel.renderable, Group)
    assert panel.subtitle is None

    assert "1 SIGNAL" in screen
    assert "Metrics: N/A" in screen
    assert "Signal: impact" in screen


@pytest.mark.parametrize(
    "tab",
    tuple(IncomingDetailTab),
)
def test_historical_tabs_remain_in_subtitle(tab):
    panel, _ = render_detail(
        tab=tab,
        use_geometry=False,
    )

    assert isinstance(panel.subtitle, Text)

    for number in "123456":
        assert number in panel.subtitle.plain


def test_v2_compact_preserves_critical_evidence():
    panel, screen = render_detail(
        terminal_height=20,
    )

    assert "impact" in screen
    assert "CRITICAL" in screen
    assert "2 MAJOR" in screen
    assert "5.87 Mbps" in screen

    assert "1 SIGNAL" in screen


def test_v2_missing_selection_does_not_substitute_signal():
    panel, screen = render_detail(selected=None)

    assert "No incoming signal selected." in screen
    assert "10.0.18.51:3000" not in screen
    assert "192.0.2.30:8050" not in screen
