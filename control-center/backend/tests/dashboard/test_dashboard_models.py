"""Pruebas de los modelos de presentación del dashboard."""

from datetime import datetime, timezone
from app.domain.streaming import HealthStatus, StreamingHealth
import pytest

from app.dashboard.models.dashboard_models import (
    DashboardData,
    PathRowData,
    ServerPanelData,
    StreamingPanelData,
)


def test_server_panel_data_stores_expected_values() -> None:
    snapshot_at = datetime(2026, 7, 20, 18, 30, tzinfo=timezone.utc)

    data = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot_at=snapshot_at,
        quality="AVAILABLE",
    )

    assert data.hostname == "server-01"
    assert data.mediamtx_online is True
    assert data.api_online is True
    assert data.snapshot_at == snapshot_at
    assert data.quality == "AVAILABLE"


def test_streaming_panel_data_stores_expected_values() -> None:
    data = StreamingPanelData(
        active_paths=2,
        readers=5,
        inbound_bitrate_bps=6_000_000,
        outbound_bitrate_bps=18_000_000,
        quality="AVAILABLE",
    )

    assert data.active_paths == 2
    assert data.readers == 5
    assert data.inbound_bitrate_bps == 6_000_000
    assert data.outbound_bitrate_bps == 18_000_000
    assert data.quality == "AVAILABLE"


def test_path_row_data_stores_expected_values() -> None:
    data = PathRowData(
        name="canal-principal",
        status="ACTIVE",
        readers=3,
        inbound_bitrate_bps=4_000_000,
        outbound_bitrate_bps=12_000_000,
        quality="AVAILABLE",
        source="udpSource",
    )

    assert data.name == "canal-principal"
    assert data.status == "ACTIVE"
    assert data.readers == 3
    assert data.source == "udpSource"


def test_dashboard_data_groups_all_sections() -> None:
    server = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot_at=None,
        quality="NOT_AVAILABLE",
    )

    streaming = StreamingPanelData(
        active_paths=0,
        readers=0,
        inbound_bitrate_bps=None,
        outbound_bitrate_bps=None,
        quality="NOT_AVAILABLE",
    )

    dashboard = DashboardData(
    server=server,
    streaming=streaming,
    paths=(),
    health=None,
    )

    assert dashboard.server is server
    assert dashboard.streaming is streaming
    assert dashboard.paths == ()
    assert dashboard.health is None


def test_streaming_panel_rejects_negative_active_paths() -> None:
    with pytest.raises(ValueError):
        StreamingPanelData(
            active_paths=-1,
            readers=0,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
        )


def test_streaming_panel_rejects_negative_readers() -> None:
    with pytest.raises(ValueError):
        StreamingPanelData(
            active_paths=0,
            readers=-1,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
        )


def test_path_row_rejects_negative_readers() -> None:
    with pytest.raises(ValueError):
        PathRowData(
            name="canal-principal",
            status="ACTIVE",
            readers=-1,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
            source="udpSource",
        )


def test_path_row_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        PathRowData(
            name="   ",
            status="ACTIVE",
            readers=0,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
            source="N/D",
        )
            
def test_dashboard_data_accepts_streaming_health() -> None:
    """DashboardData debe transportar la salud del streaming."""

    health = StreamingHealth(
        captured_at=datetime(
            2026,
            7,
            22,
            tzinfo=timezone.utc,
        ),
        paths=(),
        status=HealthStatus.UNKNOWN,
        message="Sin conexiones.",
    )

    dashboard = DashboardData(
        server=ServerPanelData(
            hostname="server-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=health.captured_at,
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=0,
            readers=0,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="AVAILABLE",
        ),
        paths=(),
        health=health,
    )

    assert dashboard.health is health

def test_dashboard_data_accepts_network_interfaces_panel() -> None:
    from app.dashboard.models import (
        NetworkInterfaceRowData,
        NetworkInterfacesPanelData,
    )

    captured_at = datetime(
        2026,
        8,
        18,
        19,
        30,
        tzinfo=timezone.utc,
    )

    network_interfaces = NetworkInterfacesPanelData(
        interfaces=(
            NetworkInterfaceRowData(
                interface="ens2f0",
                interface_type="ETHERNET",
                is_up=True,
                carrier=True,
                link_speed_mbps=100,
                mtu=1500,
                mac_address="00:e0:ed:2c:6d:c0",
                ipv4_addresses=("172.16.30.35",),
                ipv6_addresses=(),
                rx_bps=60_000.0,
                tx_bps=4_900_000.0,
                errors_in=0,
                errors_out=0,
                dropped_in=10,
                dropped_out=0,
                dropped_in_per_second=0.8,
            ),
        ),
        captured_at=captured_at,
    )

    dashboard = DashboardData(
        server=ServerPanelData(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=captured_at,
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=1,
            readers=1,
            inbound_bitrate_bps=4_000_000,
            outbound_bitrate_bps=4_000_000,
            quality="AVAILABLE",
        ),
        paths=(),
        network_interfaces=network_interfaces,
    )

    assert dashboard.network_interfaces is network_interfaces
    assert (
        dashboard.network_interfaces.interfaces[0].interface
        == "ens2f0"
    )


def test_dashboard_data_accepts_node_health_panel() -> None:
    from datetime import UTC, datetime

    from app.dashboard.models import (
        NodeHealthPanelData,
    )

    node_health = NodeHealthPanelData(
        state="WARNING",
        system_state="HEALTHY",
        network_state="WARNING",
        interfaces=(),
        captured_at=datetime(
            2026,
            8,
            18,
            23,
            50,
            tzinfo=UTC,
        ),
    )

    base = DashboardData(
        server=ServerPanelData(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=None,
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=0,
            readers=0,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
        ),
        paths=(),
        node_health=node_health,
    )

    assert base.node_health is node_health


def test_dashboard_data_accepts_recent_events_panel() -> None:
    from datetime import UTC, datetime

    from app.dashboard.models import (
        RecentEventRowData,
        RecentEventsPanelData,
    )

    recent_events = RecentEventsPanelData(
        events=(
            RecentEventRowData(
                event_id="event-001",
                event_type="NODE_HEALTH_DEGRADED",
                severity="WARNING",
                title="Node health degraded",
                occurred_at=datetime(
                    2026,
                    8,
                    20,
                    18,
                    0,
                    tzinfo=UTC,
                ),
            ),
        ),
    )

    dashboard = DashboardData(
        server=ServerPanelData(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=None,
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=0,
            readers=0,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
        ),
        paths=(),
        recent_events=recent_events,
    )

    assert dashboard.recent_events is recent_events
    assert dashboard.recent_events.event_count == 1
    assert (
        dashboard.recent_events.events[0].event_id
        == "event-001"
    )
