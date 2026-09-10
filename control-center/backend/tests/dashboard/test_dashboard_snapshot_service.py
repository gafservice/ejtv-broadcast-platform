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

def test_snapshot_preserves_active_alarms() -> None:
    from app.dashboard.models import (
        ActiveAlarmRowData,
        ActiveAlarmsPanelData,
    )

    captured_at = datetime(
        2026,
        8,
        21,
        23,
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

    active_alarms = ActiveAlarmsPanelData(
        alarms=(
            ActiveAlarmRowData(
                alarm_id="alarm-001",
                alarm_type="NODE_HEALTH_DEGRADED",
                severity="CRITICAL",
                state="ACTIVE",
                message="Node health degraded to CRITICAL",
                opened_at=captured_at,
            ),
        )
    )

    result = DashboardSnapshotService().build_snapshot(
        DashboardSnapshotInput(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
            active_alarms=active_alarms,
        )
    )

    assert result.active_alarms is active_alarms
    assert result.active_alarms.alarm_count == 1
    assert (
        result.active_alarms.alarms[0].alarm_id
        == "alarm-001"
    )


def test_snapshot_service_transports_platform_health() -> None:
    """Debe transportar PlatformHealth hasta DashboardData."""

    from app.domain.streaming.aggregation import (
        HealthPopulation,
        PlatformHealth,
    )
    from app.domain.streaming.health import HealthStatus

    captured_at = datetime(
        2026,
        9,
        9,
        21,
        15,
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

    platform_health = PlatformHealth(
        captured_at=captured_at,
        services=(),
        population=HealthPopulation(
            healthy_count=0,
            degraded_count=0,
            critical_count=0,
            unknown_count=0,
        ),
        status=HealthStatus.UNKNOWN,
        worst_observed_status=HealthStatus.UNKNOWN,
        message="No observed multimedia sessions.",
    )

    result = DashboardSnapshotService().build_snapshot(
        DashboardSnapshotInput(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
            platform_health=platform_health,
        )
    )

    assert result.platform_health is not None
    assert result.platform_health.status == "UNKNOWN"
    assert result.platform_health.worst_status == "UNKNOWN"
    assert result.platform_health.service_count == 0
    assert result.platform_health.evidence_coverage is None
    assert result.platform_health.affected_fraction is None
    assert result.platform_health.captured_at == captured_at

def test_snapshot_service_transports_rtmp_health_to_active_connections() -> None:
    """Debe transportar RTMP health hasta CONNECTED CLIENTS."""

    from app.domain.sessions import (
        ActiveSession,
        SessionMeasurement,
        SessionProtocol,
        SessionQuality,
        SessionRole,
    )
    from app.domain.streaming import HealthStatus, RTMPConnectionHealth

    captured_at = datetime(
        2026,
        9,
        10,
        18,
        10,
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

    session = ActiveSession(
        session_id="rtmp-reader-001",
        protocol=SessionProtocol.RTMP,
        role=SessionRole.READER,
        state="read",
        remote_ip="201.192.154.132",
        remote_port=50288,
        path="impact",
        connected_since=captured_at,
    )

    session_measurement = SessionMeasurement(
        captured_at=captured_at,
        sessions=(session,),
        paths=(),
        total_sessions=1,
        reader_count=1,
        publisher_count=0,
        unknown_role_count=0,
        degraded_session_count=0,
        critical_session_count=0,
        total_inbound_bitrate_mbps=0.0,
        total_outbound_bitrate_mbps=0.0,
        worst_quality=SessionQuality.UNKNOWN,
        protocols=(SessionProtocol.RTMP,),
    )

    rtmp_health = RTMPConnectionHealth(
        connection_id="rtmp-reader-001",
        path_name="impact",
        state="read",
        effective_delta_bytes=None,
        effective_bitrate_mbps=None,
        outbound_frames_discarded=None,
        status=HealthStatus.UNKNOWN,
        message="Insufficient temporal evidence.",
    )

    result = DashboardSnapshotService().build_snapshot(
        DashboardSnapshotInput(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
            session_measurement=session_measurement,
            rtmp_connections=(rtmp_health,),
        )
    )

    assert result.active_connections is not None
    assert result.active_connections.connection_count == 1
    assert result.active_connections.connections[0].health == "UNKNOWN"
