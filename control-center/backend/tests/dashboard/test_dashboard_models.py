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

def test_dashboard_data_accepts_active_alarms() -> None:
    from datetime import UTC, datetime

    from app.dashboard.models import (
        ActiveAlarmRowData,
        ActiveAlarmsPanelData,
    )

    active_alarms = ActiveAlarmsPanelData(
        alarms=(
            ActiveAlarmRowData(
                alarm_id="alarm-001",
                alarm_type="NODE_HEALTH_DEGRADED",
                severity="CRITICAL",
                state="ACTIVE",
                message="Node health degraded to CRITICAL",
                opened_at=datetime(
                    2026,
                    8,
                    21,
                    23,
                    45,
                    tzinfo=UTC,
                ),
            ),
        )
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
            quality="AVAILABLE",
        ),
        paths=(),
        active_alarms=active_alarms,
    )

    assert dashboard.active_alarms is active_alarms
    assert dashboard.active_alarms.alarm_count == 1


def test_platform_health_panel_data_stores_expected_values() -> None:
    """PlatformHealthPanelData debe preservar el resumen agregado."""

    from datetime import UTC, datetime

    from app.dashboard.models import PlatformHealthPanelData

    captured_at = datetime(
        2026,
        9,
        9,
        20,
        18,
        tzinfo=UTC,
    )

    data = PlatformHealthPanelData(
        status="DEGRADED",
        worst_status="CRITICAL",
        healthy_count=2,
        degraded_count=1,
        critical_count=1,
        unknown_count=1,
        evidence_coverage=0.8,
        affected_fraction=0.5,
        service_count=3,
        captured_at=captured_at,
    )

    assert data.status == "DEGRADED"
    assert data.worst_status == "CRITICAL"
    assert data.healthy_count == 2
    assert data.degraded_count == 1
    assert data.critical_count == 1
    assert data.unknown_count == 1
    assert data.evidence_coverage == 0.8
    assert data.affected_fraction == 0.5
    assert data.service_count == 3
    assert data.captured_at == captured_at


@pytest.mark.parametrize(
    "field_name,value",
    (
        ("healthy_count", -1),
        ("degraded_count", -1),
        ("critical_count", -1),
        ("unknown_count", -1),
        ("service_count", -1),
    ),
)
def test_platform_health_panel_data_rejects_negative_counts(
    field_name: str,
    value: int,
) -> None:
    """Los contadores de presentación no pueden ser negativos."""

    from datetime import UTC, datetime

    from app.dashboard.models import PlatformHealthPanelData

    kwargs = {
        "status": "HEALTHY",
        "worst_status": "HEALTHY",
        "healthy_count": 1,
        "degraded_count": 0,
        "critical_count": 0,
        "unknown_count": 0,
        "evidence_coverage": 1.0,
        "affected_fraction": 0.0,
        "service_count": 1,
        "captured_at": datetime(2026, 9, 9, 20, 18, tzinfo=UTC),
    }

    kwargs[field_name] = value

    with pytest.raises(ValueError):
        PlatformHealthPanelData(**kwargs)


@pytest.mark.parametrize(
    "field_name,value",
    (
        ("evidence_coverage", -0.1),
        ("evidence_coverage", 1.1),
        ("affected_fraction", -0.1),
        ("affected_fraction", 1.1),
    ),
)
def test_platform_health_panel_data_rejects_invalid_fractions(
    field_name: str,
    value: float,
) -> None:
    """Las fracciones deben permanecer dentro del intervalo 0..1."""

    from datetime import UTC, datetime

    from app.dashboard.models import PlatformHealthPanelData

    kwargs = {
        "status": "HEALTHY",
        "worst_status": "HEALTHY",
        "healthy_count": 1,
        "degraded_count": 0,
        "critical_count": 0,
        "unknown_count": 0,
        "evidence_coverage": 1.0,
        "affected_fraction": 0.0,
        "service_count": 1,
        "captured_at": datetime(2026, 9, 9, 20, 18, tzinfo=UTC),
    }

    kwargs[field_name] = value

    with pytest.raises(ValueError):
        PlatformHealthPanelData(**kwargs)


def test_platform_health_panel_data_rejects_naive_timestamp() -> None:
    """La captura mostrada debe conservar zona horaria."""

    from datetime import datetime

    from app.dashboard.models import PlatformHealthPanelData

    with pytest.raises(ValueError):
        PlatformHealthPanelData(
            status="HEALTHY",
            worst_status="HEALTHY",
            healthy_count=1,
            degraded_count=0,
            critical_count=0,
            unknown_count=0,
            evidence_coverage=1.0,
            affected_fraction=0.0,
            service_count=1,
            captured_at=datetime(2026, 9, 9, 20, 18),
        )


def test_dashboard_data_accepts_platform_health_panel() -> None:
    """DashboardData debe transportar PLATFORM HEALTH."""

    from datetime import UTC, datetime

    from app.dashboard.models import PlatformHealthPanelData

    platform_health = PlatformHealthPanelData(
        status="HEALTHY",
        worst_status="HEALTHY",
        healthy_count=2,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
        evidence_coverage=1.0,
        affected_fraction=0.0,
        service_count=2,
        captured_at=datetime(
            2026,
            9,
            9,
            20,
            18,
            tzinfo=UTC,
        ),
    )

    dashboard = DashboardData(
        server=ServerPanelData(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=platform_health.captured_at,
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=2,
            readers=2,
            inbound_bitrate_bps=8_000_000,
            outbound_bitrate_bps=8_000_000,
            quality="AVAILABLE",
        ),
        paths=(),
        platform_health=platform_health,
    )

    assert dashboard.platform_health is platform_health
