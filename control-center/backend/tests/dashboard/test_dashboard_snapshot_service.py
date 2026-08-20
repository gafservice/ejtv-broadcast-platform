"""Tests para DashboardSnapshotService."""

from datetime import UTC, datetime

from app.dashboard.models import (
    NetworkInterfaceRowData,
    NetworkInterfacesPanelData,
)
from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
    DashboardSnapshotService,
)
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    StreamingMeasurement,
)


def test_snapshot_service_transports_network_interfaces() -> None:
    captured_at = datetime(
        2026,
        8,
        18,
        19,
        45,
        tzinfo=UTC,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
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
                dropped_in=0,
                dropped_out=0,
            ),
        ),
        captured_at=captured_at,
    )

    result = DashboardSnapshotService().build_snapshot(
        DashboardSnapshotInput(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
            network_interfaces=network_interfaces,
        )
    )

    assert result.network_interfaces is network_interfaces
    assert (
        result.network_interfaces.interfaces[0].interface
        == "ens2f0"
    )


def test_snapshot_service_transports_node_health() -> None:
    from app.dashboard.models import (
        NodeHealthPanelData,
    )

    captured_at = datetime(
        2026,
        8,
        18,
        23,
        55,
        tzinfo=UTC,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    node_health = NodeHealthPanelData(
        state="WARNING",
        system_state="HEALTHY",
        network_state="WARNING",
        interfaces=(),
        captured_at=captured_at,
    )

    result = DashboardSnapshotService().build_snapshot(
        DashboardSnapshotInput(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
            node_health=node_health,
        )
    )

    assert result.node_health is node_health


def test_snapshot_service_transports_recent_events() -> None:
    from app.dashboard.models import (
        RecentEventRowData,
        RecentEventsPanelData,
    )

    captured_at = datetime(
        2026,
        8,
        20,
        19,
        0,
        tzinfo=UTC,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    recent_events = RecentEventsPanelData(
        events=(
            RecentEventRowData(
                event_id="event-001",
                event_type="NODE_HEALTH_DEGRADED",
                severity="WARNING",
                title="Node health degraded",
                occurred_at=captured_at,
            ),
        ),
    )

    result = DashboardSnapshotService().build_snapshot(
        DashboardSnapshotInput(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
            recent_events=recent_events,
        )
    )

    assert result.recent_events is recent_events
    assert result.recent_events.event_count == 1
    assert (
        result.recent_events.events[0].event_id
        == "event-001"
    )
