"""SIGNAL V2 grid and compact presentation contract."""

from io import StringIO
from unittest.mock import Mock

import pytest
from rich.console import Console, Group
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
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.renderers.incoming_signal_cards_renderer import (
    IncomingSignalCardsRenderer,
)
from app.dashboard.renderers.signal_detail_renderer import (
    SignalDetailRenderer,
)
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


def capture(renderable, *, width=122, height=None):
    output = StringIO()

    console = Console(
        file=output,
        width=width,
        force_terminal=False,
        color_system=None,
    )

    if height is None:
        console.print(renderable)
    else:
        console.print(renderable, height=height)

    return output.getvalue()


def test_v2_cards_use_expanding_grid():
    panel = IncomingSignalCardsRenderer().render(
        make_incoming(),
        selected_path_name="ejtv",
    )

    assert isinstance(panel, Panel)
    assert isinstance(panel.renderable, Table)
    assert panel.renderable.expand is True
    assert len(panel.renderable.columns) == 2


@pytest.mark.parametrize("width", (122, 140))
def test_v2_card_columns_occupy_both_halves(width):
    panel = IncomingSignalCardsRenderer().render(
        make_incoming(),
        selected_path_name="ejtv",
    )

    screen = capture(panel, width=width)
    lines = screen.splitlines()

    identification_line = next(
        line for line in lines if "IDENTIFICACIÓN" in line
    )

    reception_line = next(
        line for line in lines if "RECEPCIÓN" in line
    )

    assert identification_line == reception_line

    first_card_start = identification_line.index("╭", 1)
    second_card_start = identification_line.index(
        "╭",
        first_card_start + 1,
    )

    assert second_card_start >= int(width * 0.40)

    for title in (
        "IDENTIFICACIÓN",
        "RECEPCIÓN",
        "HEALTH",
        "ALARMAS",
    ):
        assert title in screen


def test_v2_small_geometry_requests_compact_historical_renderer():
    renderer = DashboardRenderer()

    renderer._incoming_panel_renderer = Mock()
    renderer._incoming_panel_renderer.render.return_value = Panel(
        "INCOMING LIST"
    )

    renderer._signal_detail_renderer = Mock()
    renderer._signal_detail_renderer.render.return_value = Panel(
        "HISTORICAL DETAIL"
    )

    incoming = make_incoming()

    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=20,
        signal_count=len(incoming.rows),
        maximum_visible_rows=8,
    )

    assert geometry.detail_height < 20

    data = Mock()
    data.incoming = incoming

    renderer.render(
        data,
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=IncomingSelectionState(
            selected_path_name="impact",
        ),
        incoming_visible_capacity=geometry.visible_rows,
        incoming_vertical_geometry=geometry,
        terminal_width=100,
    )

    renderer._signal_detail_renderer.render.assert_called_once_with(
        incoming,
        selected_path_name="impact",
        compact=True,
    )


def test_historical_call_without_v2_geometry_preserves_compact_flag():
    renderer = DashboardRenderer()

    renderer._incoming_panel_renderer = Mock()
    renderer._incoming_panel_renderer.render.return_value = Panel(
        "INCOMING LIST"
    )

    renderer._signal_detail_renderer = Mock()
    renderer._signal_detail_renderer.render.return_value = Panel(
        "HISTORICAL DETAIL"
    )

    incoming = make_incoming()
    data = Mock()
    data.incoming = incoming

    renderer.render(
        data,
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=IncomingSelectionState(
            selected_path_name="ejtv",
        ),
        incoming_visible_capacity=5,
        terminal_width=100,
    )

    renderer._signal_detail_renderer.render.assert_called_once_with(
        incoming,
        selected_path_name="ejtv",
        compact=False,
    )


def test_compact_detail_preserves_critical_operational_evidence():
    incoming = make_incoming()

    panel = SignalDetailRenderer().render(
        incoming,
        selected_path_name="impact",
        compact=True,
    )

    screen = capture(
        panel,
        width=100,
        height=12,
    )

    assert "impact" in screen
    assert "CRITICAL" in screen
    assert "2 MAJOR" in screen
    assert "5.87 Mbps" in screen
