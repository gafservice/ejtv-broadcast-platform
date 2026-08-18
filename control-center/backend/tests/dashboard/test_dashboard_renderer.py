"""Pruebas para DashboardRenderer."""
from rich.console import Console

from app.domain.streaming import HealthStatus, StreamingHealth

from datetime import datetime, timezone

from rich.layout import Layout

from app.dashboard.models import (
    DashboardData,
    PathRowData,
    ServerPanelData,
    SessionPanelData,
    StreamingPanelData,
)
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer


def build_dashboard_data() -> DashboardData:
    """Construye datos válidos para las pruebas del renderer."""

    return DashboardData(
        server=ServerPanelData(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=datetime(
                2026,
                7,
                21,
                14,
                0,
                tzinfo=timezone.utc,
            ),
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=1,
            readers=5,
            inbound_bitrate_bps=8_000_000,
            outbound_bitrate_bps=40_000_000,
            quality="AVAILABLE",
        ),
        paths=(
            PathRowData(
                name="enlace",
                source="UDP",
                readers=5,
                inbound_bitrate_bps=8_000_000,
                outbound_bitrate_bps=40_000_000,
                status="ACTIVE",
                quality="AVAILABLE",
            ),
        ),
        health=None,
    )


def test_dashboard_renderer_can_be_created() -> None:
    renderer = DashboardRenderer()

    assert renderer is not None


def test_render_returns_rich_layout() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    layout = renderer.render(data)

    assert isinstance(layout, Layout)
def test_render_contains_health_panel() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        color_system=None,
    )
    console.print(layout)

    output = console.export_text()

    assert "STREAM HEALTH" in output
    assert "UNKNOWN" in output
    assert "No health data available." in output


def test_render_contains_streaming_health_data() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    health = StreamingHealth(
        captured_at=data.server.snapshot_at,
        paths=(),
        status=HealthStatus.HEALTHY,
        message="El subsistema SRT funciona correctamente.",
    )

    data = DashboardData(
        server=data.server,
        streaming=data.streaming,
        paths=data.paths,
        health=health,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        color_system=None,
    )
    console.print(layout)

    output = console.export_text()

    assert "STREAM HEALTH" in output
    assert "HEALTHY" in output
    assert "Summary" in output
    assert "El subsistema SRT funciona" in output
    assert "…" in output


def test_render_contains_active_clients_panel() -> None:
    """Debe renderizar ACTIVE CLIENTS cuando hay datos de sesiones."""

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        sessions=SessionPanelData(
            total_sessions=6,
            readers=5,
            publishers=1,
            degraded_sessions=1,
            critical_sessions=0,
            inbound_bitrate_bps=8_000_000,
            outbound_bitrate_bps=40_000_000,
            quality="GOOD",
            protocol_counts=(
                ("SRT", 3),
                ("RTMP", 1),
                ("RTSP", 1),
                ("HLS", 1),
                ("WebRTC", 0),
                ("UNKNOWN", 0),
            ),
        ),
        health=base_data.health,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        color_system=None,
    )
    console.print(layout)

    output = console.export_text()

    assert "ACTIVE CLIENTS" in output

    assert "SRT" in output
    assert "RTMP" in output
    assert "RTSP" in output
    assert "HLS" in output
    assert "WebRTC" in output

    assert "TOTAL" in output

    assert "Inbound" in output
    assert "Outbound" in output
    assert "GOOD" not in output

    assert "Sessions" not in output
    assert "Publishers" not in output
    assert "Degraded" not in output
    assert "Critical" not in output

def test_render_contains_network_interfaces_panel() -> None:
    from app.dashboard.models import (
        NetworkInterfaceRowData,
        NetworkInterfacesPanelData,
    )

    renderer = DashboardRenderer()
    base_data = build_dashboard_data()

    network_interfaces = NetworkInterfacesPanelData(
        interfaces=(
            NetworkInterfaceRowData(
                interface="enp9s0",
                interface_type="ETHERNET",
                is_up=True,
                carrier=True,
                link_speed_mbps=1000,
                mtu=1500,
                mac_address="3c:07:54:7c:b5:88",
                ipv4_addresses=("10.0.18.54",),
                ipv6_addresses=(),
                rx_bps=9_000_000.0,
                tx_bps=418.0,
                errors_in=0,
                errors_out=0,
                dropped_in=0,
                dropped_out=0,
                dropped_in_per_second=0.0,
            ),
            NetworkInterfaceRowData(
                interface="ens2f1",
                interface_type="ETHERNET",
                is_up=False,
                carrier=False,
                link_speed_mbps=None,
                mtu=1500,
                mac_address="00:e0:ed:2c:6d:c1",
                ipv4_addresses=(),
                ipv6_addresses=(),
                rx_bps=0.0,
                tx_bps=0.0,
                errors_in=0,
                errors_out=0,
                dropped_in=0,
                dropped_out=0,
                dropped_in_per_second=0.0,
            ),
        ),
        captured_at=base_data.server.snapshot_at,
    )

    data = DashboardData(
        server=base_data.server,
        streaming=base_data.streaming,
        paths=base_data.paths,
        health=base_data.health,
        network_interfaces=network_interfaces,
    )

    layout = renderer.render(data)

    console = Console(
        record=True,
        width=160,
        height=60,
        color_system=None,
    )

    console.print(layout)

    output = console.export_text()

    assert "NETWORK INTERFACES" in output
    assert "enp9s0" in output
    assert "ens2f1" in output
    assert "1 Gbps" in output
    assert "9.00 Mbps" in output
    assert "DOWN" in output


def test_render_preserves_legacy_layout_without_network_interfaces() -> None:
    renderer = DashboardRenderer()
    data = build_dashboard_data()

    layout = renderer.render(data)

    assert data.network_interfaces is None

    console = Console(
        record=True,
        width=160,
        height=60,
        color_system=None,
    )

    console.print(layout)

    output = console.export_text()

    assert "NETWORK INTERFACES" not in output
