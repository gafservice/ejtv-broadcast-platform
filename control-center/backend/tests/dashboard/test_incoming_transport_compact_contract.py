"""Compact TRANSPORT presentation contract for INCOMING V2."""

from io import StringIO

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)
from app.domain.streaming.health import HealthStatus


def make_data():
    return IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="UDP",
                protocol="UDP",
                status="ACTIVE",
                bitrate_receive_mbps=2.21,
                health_status=HealthStatus.DEGRADED,
                transport_health_status=HealthStatus.HEALTHY,
                remote_address="10.0.18.51:3000",
            ),
        )
    )


def render_compact():
    panel = IncomingTransportCardsRenderer().render(
        make_data(),
        selected_path_name="ejtv",
        compact=True,
    )

    output = StringIO()

    console = Console(
        file=output,
        width=122,
        force_terminal=False,
        color_system=None,
    )

    console.print(panel, height=16)

    return panel, output.getvalue()


def test_compact_transport_uses_table():
    panel, _ = render_compact()

    assert isinstance(panel, Panel)
    assert isinstance(panel.renderable, Table)
    assert panel.title == "TRANSPORT DETAIL"


def test_compact_transport_preserves_canonical_health():
    _, screen = render_compact()

    assert "Transport Health" in screen
    assert "HEALTHY" in screen
    assert "DEGRADED" not in screen


def test_compact_transport_preserves_connection_evidence():
    _, screen = render_compact()

    assert "ejtv" in screen
    assert "UDP" in screen
    assert "10.0.18.51:3000" in screen
    assert "2.21 Mbps" in screen


def test_compact_transport_keeps_unavailable_explicit():
    _, screen = render_compact()

    assert "Packet Loss" in screen
    assert "RTT" in screen
    assert "N/A" in screen
