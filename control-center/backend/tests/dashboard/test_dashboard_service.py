"""Pruebas del DashboardService."""

from datetime import datetime, timezone

from app.domain.sessions import (
    ActiveSession,
    SessionMeasurement,
    SessionProtocol,
    SessionQuality,
    SessionRole,
)


from datetime import timedelta

from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInfo,
    NetworkInterfaceInfo,
    NetworkInterfaceTelemetry,
    NetworkInterfaceType,
    NetworkRate,
    SystemResources,
    UptimeInfo,
)

import pytest

from app.dashboard.services.dashboard_service import DashboardService
from app.dashboard.models.panel_viewport import PanelViewport
from app.domain.sessions.measurement import SessionMeasurement
from app.domain.sessions.quality import SessionQuality

from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
    StreamingMeasurement,
    StreamingPathMeasurement,
)

def test_build_system_panel_calculates_network_rates() -> None:
    """Debe calcular RX/TX usando dos capturas consecutivas."""

    service = DashboardService()

    captured_at = datetime(
        2026,
        7,
        20,
        12,
        0,
        tzinfo=timezone.utc,
    )

    previous = SystemResources(
        cpu=CPUInfo(
            usage_percent=10,
            per_core_usage_percent=(10,),
            logical_cores=1,
            physical_cores=1,
            frequency_mhz=3000,
        ),
        memory=MemoryInfo(
            total_bytes=100,
            available_bytes=40,
            used_bytes=60,
            usage_percent=60,
        ),
        disk=DiskInfo(
            total_bytes=100,
            used_bytes=50,
            free_bytes=50,
            usage_percent=50,
        ),
        network=NetworkInfo(
            interface="ens2f0",
            bytes_sent=500_000,
            bytes_received=1_000_000,
            packets_sent=0,
            packets_received=0,
            errors_in=1,
            errors_out=2,
            dropped_in=3,
            dropped_out=4,
        ),
        uptime=UptimeInfo(
            uptime_seconds=100,
        ),
        captured_at=captured_at,
    )

    current = SystemResources(
        cpu=previous.cpu,
        memory=previous.memory,
        disk=previous.disk,
        network=NetworkInfo(
            interface="ens2f0",
            bytes_sent=1_000_000,
            bytes_received=2_000_000,
            packets_sent=0,
            packets_received=0,
            errors_in=5,
            errors_out=6,
            dropped_in=7,
            dropped_out=8,
        ),
        uptime=UptimeInfo(
            uptime_seconds=101,
        ),
        captured_at=captured_at + timedelta(seconds=1),
    )

    panel = service.build_system_panel(
        resources=current,
        previous_resources=previous,
    )

    assert panel.network.rx_bps == 8_000_000
    assert panel.network.tx_bps == 4_000_000

    assert panel.network.errors_in == 5
    assert panel.network.errors_out == 6

    assert panel.network.dropped_in == 7
    assert panel.network.dropped_out == 8

    assert panel.network.errors_in_per_second == 4.0
    assert panel.network.errors_out_per_second == 4.0
    assert panel.network.dropped_in_per_second == 4.0
    assert panel.network.dropped_out_per_second == 4.0

def test_dashboard_service_can_be_created() -> None:
    service = DashboardService()

    assert service is not None


def test_build_server_panel_data() -> None:
    service = DashboardService()

    captured_at = datetime(
        2026,
        7,
        20,
        19,
        45,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    data = service.build_server_panel(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    assert data.hostname == "server-01"
    assert data.mediamtx_online is True
    assert data.api_online is True
    assert data.snapshot_at == captured_at
    assert data.quality == "NOT_AVAILABLE"


def test_build_streaming_panel_data() -> None:
    service = DashboardService()

    data = service.build_streaming_panel(
        active_paths=2,
        readers=5,
        inbound_bitrate_bps=6_000_000,
        outbound_bitrate_bps=18_000_000,
        quality=MeasurementQuality.AVAILABLE,
    )

    assert data.active_paths == 2
    assert data.readers == 5
    assert data.inbound_bitrate_bps == 6_000_000
    assert data.outbound_bitrate_bps == 18_000_000
    assert data.quality == "AVAILABLE"


def test_build_path_row_data() -> None:
    service = DashboardService()

    data = service.build_path_row(
        name="canal-principal",
        status="ACTIVE",
        readers=3,
        inbound_bitrate_bps=4_000_000,
        outbound_bitrate_bps=12_000_000,
        quality=MeasurementQuality.AVAILABLE,
        source="udpSource",
    )

    assert data.name == "canal-principal"
    assert data.status == "ACTIVE"
    assert data.readers == 3
    assert data.inbound_bitrate_bps == 4_000_000
    assert data.outbound_bitrate_bps == 12_000_000
    assert data.quality == "AVAILABLE"
    assert data.source == "udpSource"


def test_build_dashboard_data() -> None:
    service = DashboardService()

    captured_at = datetime(
        2026,
        7,
        20,
        20,
        30,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    server = service.build_server_panel(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    streaming = service.build_streaming_panel(
        active_paths=1,
        readers=2,
        inbound_bitrate_bps=4_000_000,
        outbound_bitrate_bps=8_000_000,
        quality=MeasurementQuality.AVAILABLE,
    )

    path = service.build_path_row(
        name="canal-principal",
        status="ACTIVE",
        readers=2,
        inbound_bitrate_bps=4_000_000,
        outbound_bitrate_bps=8_000_000,
        quality=MeasurementQuality.AVAILABLE,
        source="udpSource",
    )

    dashboard = service.build_dashboard(
        server=server,
        streaming=streaming,
        paths=(path,),
    )

    assert dashboard.server is server
    assert dashboard.streaming is streaming
    assert dashboard.paths == (path,)


def test_build_dashboard_accepts_empty_paths() -> None:
    service = DashboardService()

    captured_at = datetime(
        2026,
        7,
        20,
        21,
        0,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    server = service.build_server_panel(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    streaming = service.build_streaming_panel(
        active_paths=0,
        readers=0,
        inbound_bitrate_bps=None,
        outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    dashboard = service.build_dashboard(
        server=server,
        streaming=streaming,
        paths=(),
    )

    assert dashboard.paths == ()
    assert dashboard.streaming.active_paths == 0
    assert dashboard.streaming.readers == 0


def test_build_dashboard_from_measurement() -> None:
    service = DashboardService()

    previous_at = datetime(
        2026,
        7,
        20,
        20,
        29,
        59,
        tzinfo=timezone.utc,
    )

    captured_at = datetime(
        2026,
        7,
        20,
        20,
        30,
        tzinfo=timezone.utc,
    )

    media_path = MediaPath(
        name="canal-principal",
        configuration_name="canal-principal",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="udpSource",
            source_id="source-001",
        ),
        readers=(),
        inbound_bytes=4_000_000,
        outbound_bytes=8_000_000,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(media_path,),
        reported_item_count=1,
        reported_page_count=1,
    )

    path_measurement = StreamingPathMeasurement(
        name="canal-principal",
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=0,
        reader_delta=0,
        inbound_delta_bytes=500_000,
        outbound_delta_bytes=1_000_000,
        inbound_bitrate_bps=4_000_000,
        outbound_bitrate_bps=8_000_000,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=previous_at,
        interval_seconds=1.0,
        paths=(path_measurement,),
        total_inbound_bitrate_bps=4_000_000,
        total_outbound_bitrate_bps=8_000_000,
        quality=MeasurementQuality.AVAILABLE,
    )

    dashboard = service.build_dashboard_from_measurement(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        measurement=measurement,
    )

    assert dashboard.server.hostname == "server-01"
    assert dashboard.server.mediamtx_online is True
    assert dashboard.server.api_online is True
    assert dashboard.server.snapshot_at == captured_at
    assert dashboard.server.quality == "AVAILABLE"

    assert dashboard.streaming.active_paths == 1
    assert dashboard.streaming.readers == 0
    assert dashboard.streaming.inbound_bitrate_bps == 4_000_000
    assert dashboard.streaming.outbound_bitrate_bps == 8_000_000
    assert dashboard.streaming.quality == "AVAILABLE"

    assert len(dashboard.paths) == 1

    path = dashboard.paths[0]

    assert path.name == "canal-principal"
    assert path.status == "ACTIVE"
    assert path.readers == 0
    assert path.inbound_bitrate_bps == 4_000_000
    assert path.outbound_bitrate_bps == 8_000_000
    assert path.quality == "AVAILABLE"
    assert path.source == "UDP"


def test_build_dashboard_uses_none_source_when_path_is_missing() -> None:
    service = DashboardService()

    previous_at = datetime(
        2026,
        7,
        20,
        20,
        29,
        59,
        tzinfo=timezone.utc,
    )

    captured_at = datetime(
        2026,
        7,
        20,
        20,
        30,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    path_measurement = StreamingPathMeasurement(
        name="canal-ausente",
        status=MediaPathStatus.OFFLINE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=0,
        reader_delta=0,
        inbound_delta_bytes=0,
        outbound_delta_bytes=0,
        inbound_bitrate_bps=0,
        outbound_bitrate_bps=0,
        state_changed=True,
        quality=MeasurementQuality.AVAILABLE,
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=previous_at,
        interval_seconds=1.0,
        paths=(path_measurement,),
        total_inbound_bitrate_bps=0,
        total_outbound_bitrate_bps=0,
        quality=MeasurementQuality.AVAILABLE,
    )

    dashboard = service.build_dashboard_from_measurement(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        measurement=measurement,
    )

    assert len(dashboard.paths) == 1
    assert dashboard.paths[0].name == "canal-ausente"
    assert dashboard.paths[0].status == "OFFLINE"
    assert dashboard.paths[0].source == "NONE"


def test_build_dashboard_uses_none_source_when_path_has_no_source() -> None:
    service = DashboardService()

    previous_at = datetime(
        2026,
        7,
        20,
        20,
        29,
        59,
        tzinfo=timezone.utc,
    )

    captured_at = datetime(
        2026,
        7,
        20,
        20,
        30,
        tzinfo=timezone.utc,
    )

    media_path = MediaPath(
        name="canal-sin-fuente",
        configuration_name="canal-sin-fuente",
        status=MediaPathStatus.NO_SOURCE,
        ready=False,
        available=False,
        online=False,
        source=None,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(media_path,),
        reported_item_count=1,
        reported_page_count=1,
    )

    path_measurement = StreamingPathMeasurement(
        name="canal-sin-fuente",
        status=MediaPathStatus.NO_SOURCE,
        previous_status=MediaPathStatus.NO_SOURCE,
        reader_count=0,
        reader_delta=None,
        inbound_delta_bytes=None,
        outbound_delta_bytes=None,
        inbound_bitrate_bps=None,
        outbound_bitrate_bps=None,
        state_changed=False,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(path_measurement,),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    dashboard = service.build_dashboard_from_measurement(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        measurement=measurement,
    )

    assert len(dashboard.paths) == 1
    assert dashboard.paths[0].name == "canal-sin-fuente"
    assert dashboard.paths[0].status == "NO_SOURCE"
    assert dashboard.paths[0].source == "NONE"
    assert dashboard.paths[0].quality == "NOT_AVAILABLE"


def test_build_dashboard_rejects_mismatched_capture_times() -> None:
    service = DashboardService()

    snapshot_at = datetime(
        2026,
        7,
        20,
        20,
        30,
        tzinfo=timezone.utc,
    )

    measurement_at = datetime(
        2026,
        7,
        20,
        20,
        30,
        1,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=snapshot_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    measurement = StreamingMeasurement(
        captured_at=measurement_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    with pytest.raises(
        ValueError,
        match="snapshot y measurement deben pertenecer al mismo instante",
    ):
        service.build_dashboard_from_measurement(
            hostname="server-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
        )


def test_build_dashboard_rejects_duplicate_measurement_paths() -> None:
    service = DashboardService()

    previous_at = datetime(
        2026,
        7,
        20,
        20,
        29,
        59,
        tzinfo=timezone.utc,
    )

    captured_at = datetime(
        2026,
        7,
        20,
        20,
        30,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    first_path = StreamingPathMeasurement(
        name="canal-duplicado",
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=1,
        reader_delta=0,
        inbound_delta_bytes=500_000,
        outbound_delta_bytes=500_000,
        inbound_bitrate_bps=4_000_000,
        outbound_bitrate_bps=4_000_000,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )

    second_path = StreamingPathMeasurement(
        name="canal-duplicado",
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=2,
        reader_delta=1,
        inbound_delta_bytes=600_000,
        outbound_delta_bytes=1_200_000,
        inbound_bitrate_bps=4_800_000,
        outbound_bitrate_bps=9_600_000,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=previous_at,
        interval_seconds=1.0,
        paths=(first_path, second_path),
        total_inbound_bitrate_bps=8_800_000,
        total_outbound_bitrate_bps=13_600_000,
        quality=MeasurementQuality.AVAILABLE,
    )

    with pytest.raises(
        ValueError,
        match="measurement contiene nombres de paths duplicados",
    ):
        service.build_dashboard_from_measurement(
            hostname="server-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
        )


def test_build_dashboard_rejects_mismatched_health_capture_time() -> None:
    """Health debe corresponder al mismo instante que el snapshot."""

    from datetime import timedelta

    from app.domain.streaming import HealthStatus, StreamingHealth

    service = DashboardService()

    captured_at = datetime(
        2026,
        7,
        22,
        12,
        0,
        tzinfo=timezone.utc,
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

    health = StreamingHealth(
        captured_at=captured_at + timedelta(seconds=1),
        paths=(),
        status=HealthStatus.UNKNOWN,
        message="Sin métricas.",
    )

    with pytest.raises(
        ValueError,
        match="deben pertenecer al mismo instante",
    ):
        service.build_dashboard_from_measurement(
            hostname="server-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
            health=health,
        )

def test_resolve_source_formats_mpegts_source() -> None:
    service = DashboardService()

    captured_at = datetime(
        2026,
        7,
        20,
        20,
        30,
        tzinfo=timezone.utc,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(
            MediaPath(
                name="canal-mpegts",
                configuration_name="canal-mpegts",
                status=MediaPathStatus.ACTIVE,
                ready=True,
                available=True,
                online=True,
                source=MediaSource(
                    source_type="mpegtsSource",
                    source_id="source-mpegts-001",
                ),
                readers=(),
                inbound_bytes=0,
                outbound_bytes=0,
            ),
        ),
        reported_item_count=1,
        reported_page_count=1,
    )

    source = service._resolve_source(
        snapshot=snapshot,
        path_name="canal-mpegts",
    )

    assert source == "MPEG-TS"

def test_build_session_panel_data() -> None:
    """Debe convertir SessionMeasurement en SessionPanelData."""

    captured_at = datetime(
        2026,
        7,
        24,
        14,
        0,
        tzinfo=timezone.utc,
    )

    quality = tuple(SessionQuality)[0]

    measurement = SessionMeasurement(
        captured_at=captured_at,
        sessions=(),
        paths=(),
        total_sessions=0,
        reader_count=0,
        publisher_count=0,
        unknown_role_count=0,
        degraded_session_count=0,
        critical_session_count=0,
        total_inbound_bitrate_mbps=8.5,
        total_outbound_bitrate_mbps=42.25,
        worst_quality=quality,
        protocols=(),
    )

    panel = DashboardService().build_session_panel(
        measurement=measurement,
    )

    assert panel.total_sessions == 0
    assert panel.readers == 0
    assert panel.publishers == 0
    assert panel.degraded_sessions == 0
    assert panel.critical_sessions == 0
    assert panel.inbound_bitrate_bps == 8_500_000
    assert panel.outbound_bitrate_bps == 42_250_000
    assert panel.quality == quality.value

def test_build_active_connections_panel_data() -> None:
    """Debe convertir las sesiones activas en filas del panel."""

    captured_at = datetime(
        2026,
        7,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )

    session = ActiveSession(
        session_id="session-001",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="active",
        remote_ip="201.192.154.130",
        remote_port=26676,
        path="canal-principal",
        connected_since=datetime(
            2026,
            7,
            26,
            17,
            0,
            tzinfo=timezone.utc,
        ),
        country_name="Costa Rica",
        bitrate_send_mbps=4.31,
        username="cliente-norte",
    )

    measurement = SessionMeasurement(
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
        total_outbound_bitrate_mbps=4.31,
        worst_quality=SessionQuality.GOOD,
        protocols=(SessionProtocol.SRT,),
    )

    panel = DashboardService().build_active_connections_panel(
        measurement=measurement,
    )

    assert panel.captured_at == captured_at
    assert panel.connection_count == 1

    connection = panel.connections[0]

    assert connection.remote_address == "201.192.154.130:26676"
    assert connection.country == "Costa Rica"
    assert connection.protocol == "SRT"
    assert connection.path == "canal-principal"
    assert connection.role == "READER"
    assert connection.bitrate_bps == pytest.approx(4_310_000)
    assert connection.uptime_seconds == 3_600
    assert connection.username == "cliente-norte"


def test_build_active_connections_panel_handles_missing_values() -> None:
    """Debe presentar valores seguros cuando faltan datos opcionales."""

    captured_at = datetime(
        2026,
        7,
        26,
        18,
        0,
        tzinfo=timezone.utc,
    )

    session = ActiveSession(
        session_id="session-002",
        protocol=SessionProtocol.UNKNOWN,
        role=SessionRole.UNKNOWN,
        state="active",
        remote_ip="10.20.30.15",
        remote_port=None,
        path=None,
        connected_since=captured_at,
    )

    measurement = SessionMeasurement(
        captured_at=captured_at,
        sessions=(session,),
        paths=(),
        total_sessions=1,
        reader_count=0,
        publisher_count=0,
        unknown_role_count=1,
        degraded_session_count=0,
        critical_session_count=0,
        total_inbound_bitrate_mbps=0.0,
        total_outbound_bitrate_mbps=0.0,
        worst_quality=SessionQuality.UNKNOWN,
        protocols=(SessionProtocol.UNKNOWN,),
    )

    panel = DashboardService().build_active_connections_panel(
        measurement=measurement,
    )

    connection = panel.connections[0]

    assert connection.remote_address == "10.20.30.15"
    assert connection.country == "Red local"
    assert connection.path == "(sin path)"
    assert connection.bitrate_bps is None
    assert connection.uptime_seconds == 0
    assert connection.username is None

def make_network_interface_telemetry(
    interface: str,
    *,
    interface_type: NetworkInterfaceType = (
        NetworkInterfaceType.ETHERNET
    ),
    is_up: bool = True,
    carrier: bool | None = True,
    link_speed_mbps: int | None = 1000,
    rx_bps: float | None = 1_000_000.0,
    tx_bps: float | None = 2_000_000.0,
    dropped_in_per_second: float | None = 0.5,
) -> NetworkInterfaceTelemetry:
    captured_at = datetime(
        2026,
        8,
        18,
        19,
        0,
        tzinfo=timezone.utc,
    )

    info = NetworkInterfaceInfo(
        interface=interface,
        interface_type=interface_type,
        is_up=is_up,
        carrier=carrier,
        mtu=1500,
        mac_address="00:11:22:33:44:55",
        link_speed_mbps=link_speed_mbps,
        duplex="full" if link_speed_mbps is not None else None,
        ipv4_addresses=("10.0.0.1",),
        ipv6_addresses=(),
    )

    counters = NetworkInfo(
        interface=interface,
        bytes_sent=2_000_000,
        bytes_received=1_000_000,
        packets_sent=20_000,
        packets_received=10_000,
        errors_in=1,
        errors_out=2,
        dropped_in=3,
        dropped_out=4,
    )

    rates = NetworkRate(
        interface=interface,
        rx_bps=rx_bps,
        tx_bps=tx_bps,
        interval_seconds=1.0,
        errors_in=1,
        errors_out=2,
        dropped_in=3,
        dropped_out=4,
        captured_at=captured_at,
        errors_in_per_second=0.0,
        errors_out_per_second=0.0,
        dropped_in_per_second=dropped_in_per_second,
        dropped_out_per_second=0.0,
    )

    return NetworkInterfaceTelemetry(
        info=info,
        counters=counters,
        captured_at=captured_at,
        rates=rates,
    )


def test_build_network_interfaces_panel() -> None:
    service = DashboardService()

    telemetry = (
        make_network_interface_telemetry(
            "enp9s0",
            link_speed_mbps=1000,
            rx_bps=9_000_000.0,
            tx_bps=100_000.0,
        ),
        make_network_interface_telemetry(
            "ens2f0",
            link_speed_mbps=100,
            rx_bps=60_000.0,
            tx_bps=4_900_000.0,
            dropped_in_per_second=0.8,
        ),
    )

    panel = service.build_network_interfaces_panel(
        telemetry=telemetry,
    )

    assert len(panel.interfaces) == 2

    assert tuple(
        row.interface
        for row in panel.interfaces
    ) == (
        "enp9s0",
        "ens2f0",
    )

    first = panel.interfaces[0]

    assert first.interface_type == "ETHERNET"
    assert first.is_up is True
    assert first.carrier is True
    assert first.link_speed_mbps == 1000
    assert first.rx_bps == 9_000_000.0
    assert first.tx_bps == 100_000.0

    second = panel.interfaces[1]

    assert second.link_speed_mbps == 100
    assert second.rx_bps == 60_000.0
    assert second.tx_bps == 4_900_000.0
    assert second.dropped_in_per_second == 0.8

    assert panel.captured_at == telemetry[0].rates.captured_at


def test_build_network_interfaces_panel_rejects_non_tuple() -> None:
    service = DashboardService()

    with pytest.raises(TypeError):
        service.build_network_interfaces_panel(
            telemetry=[  # type: ignore[arg-type]
                make_network_interface_telemetry(
                    "ens2f0"
                ),
            ],
        )


def test_build_dashboard_transports_network_interfaces() -> None:
    service = DashboardService()

    telemetry = (
        make_network_interface_telemetry(
            "ens2f0"
        ),
    )

    network_interfaces = service.build_network_interfaces_panel(
        telemetry=telemetry,
    )

    captured_at = telemetry[0].rates.captured_at

    server = service.build_server_panel(
        hostname="ejtv-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=MediaMTXSnapshot(
            captured_at=captured_at,
            paths=(),
            reported_item_count=0,
            reported_page_count=0,
        ),
        quality=MeasurementQuality.AVAILABLE,
    )

    streaming = service.build_streaming_panel(
        active_paths=0,
        readers=0,
        inbound_bitrate_bps=None,
        outbound_bitrate_bps=None,
        quality=MeasurementQuality.AVAILABLE,
    )

    dashboard = service.build_dashboard(
        server=server,
        streaming=streaming,
        paths=(),
        network_interfaces=network_interfaces,
    )

    assert dashboard.network_interfaces is network_interfaces


def test_build_node_health_panel_from_diagnostic() -> None:
    from app.noc.domain.network_interface_health import (
        NetworkInterfaceHealth,
    )
    from app.noc.domain.node_health import (
        NodeHealth,
        NodeHealthState,
    )
    from app.noc.domain.node_health_diagnostic import (
        NodeHealthDiagnostic,
    )

    captured_at = datetime(
        2026,
        8,
        18,
        23,
        45,
        tzinfo=timezone.utc,
    )

    diagnostic = NodeHealthDiagnostic(
        captured_at=captured_at,
        health=NodeHealth(
            NodeHealthState.WARNING
        ),
        system_health=NodeHealth(
            NodeHealthState.HEALTHY
        ),
        network_health=NodeHealth(
            NodeHealthState.WARNING
        ),
        network_interfaces=(
            NetworkInterfaceHealth(
                interface="enp9s0",
                state=NodeHealthState.HEALTHY,
                observed_at=captured_at,
                reason="Interface operating normally",
            ),
            NetworkInterfaceHealth(
                interface="ens2f0",
                state=NodeHealthState.WARNING,
                observed_at=captured_at,
                reason=(
                    "Elevated network error or drop rate"
                ),
                error_rate=0.25,
                drop_rate=1.50,
            ),
        ),
    )

    panel = DashboardService().build_node_health_panel(
        diagnostic=diagnostic,
    )

    assert panel.state == "WARNING"
    assert panel.system_state == "HEALTHY"
    assert panel.network_state == "WARNING"
    assert panel.captured_at == captured_at

    assert panel.interface_count == 2

    assert panel.interfaces[0].interface == "enp9s0"
    assert panel.interfaces[0].state == "HEALTHY"

    assert panel.interfaces[1].interface == "ens2f0"
    assert panel.interfaces[1].state == "WARNING"
    assert (
        panel.interfaces[1].reason
        == "Elevated network error or drop rate"
    )
    assert panel.interfaces[1].error_rate == 0.25
    assert panel.interfaces[1].drop_rate == 1.50


def test_build_node_health_panel_accepts_no_interfaces() -> None:
    from app.noc.domain.node_health import (
        NodeHealth,
        NodeHealthState,
    )
    from app.noc.domain.node_health_diagnostic import (
        NodeHealthDiagnostic,
    )

    captured_at = datetime(
        2026,
        8,
        18,
        23,
        45,
        tzinfo=timezone.utc,
    )

    diagnostic = NodeHealthDiagnostic(
        captured_at=captured_at,
        health=NodeHealth(
            NodeHealthState.UNKNOWN
        ),
        system_health=NodeHealth(
            NodeHealthState.UNKNOWN
        ),
        network_health=NodeHealth(
            NodeHealthState.UNKNOWN
        ),
        network_interfaces=(),
    )

    panel = DashboardService().build_node_health_panel(
        diagnostic=diagnostic,
    )

    assert panel.state == "UNKNOWN"
    assert panel.interface_count == 0


def test_build_node_health_panel_rejects_invalid_type() -> None:
    with pytest.raises(TypeError):
        DashboardService().build_node_health_panel(
            diagnostic=object(),  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# RECENT EVENTS
# ---------------------------------------------------------------------------

def test_build_recent_events_panel() -> None:
    from datetime import datetime, timezone

    from app.noc.domain.node_event import (
        EventRecord,
        EventSeverity,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    source = NodeInstanceId(
        "streaming-primary"
    )

    older = EventRecord(
        event_id="event-001",
        event_type="NODE_HEALTH_DEGRADED",
        severity=EventSeverity.WARNING,
        timestamp=datetime(
            2026,
            8,
            20,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        source=source,
        title="Node health degraded",
        description="Health degraded",
    )

    newer = EventRecord(
        event_id="event-002",
        event_type="NODE_HEALTH_RECOVERED",
        severity=EventSeverity.INFO,
        timestamp=datetime(
            2026,
            8,
            20,
            19,
            0,
            tzinfo=timezone.utc,
        ),
        source=source,
        title="Node health recovered",
        description="Health recovered",
    )

    panel = service.build_recent_events_panel(
        events=(
            older,
            newer,
        ),
    )

    assert panel.event_count == 2

    assert (
        panel.events[0].event_id
        == "event-002"
    )

    assert (
        panel.events[1].event_id
        == "event-001"
    )

    assert (
        panel.events[0].severity
        == "INFO"
    )

    assert (
        panel.events[0].occurred_at
        == newer.timestamp
    )


def test_build_recent_events_panel_limits_results() -> None:
    from datetime import datetime, timedelta, timezone

    from app.noc.domain.node_event import (
        EventRecord,
        EventSeverity,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    source = NodeInstanceId(
        "streaming-primary"
    )

    base = datetime(
        2026,
        8,
        20,
        18,
        0,
        tzinfo=timezone.utc,
    )

    events = tuple(
        EventRecord(
            event_id=f"event-{index}",
            event_type="NODE_HEALTH_DEGRADED",
            severity=EventSeverity.WARNING,
            timestamp=(
                base
                + timedelta(
                    minutes=index
                )
            ),
            source=source,
            title=f"Event {index}",
            description=f"Event {index}",
        )
        for index in range(10)
    )

    panel = service.build_recent_events_panel(
        events=events,
        viewport=PanelViewport(
            offset=0,
            page_size=5,
        ),
    )

    assert panel.event_count == 5

    assert tuple(
        event.event_id
        for event in panel.events
    ) == (
        "event-9",
        "event-8",
        "event-7",
        "event-6",
        "event-5",
    )


def test_build_recent_events_panel_accepts_empty_events() -> None:
    service = DashboardService()

    panel = service.build_recent_events_panel(
        events=(),
    )

    assert panel.events == ()
    assert panel.event_count == 0
    assert panel.is_empty is True


def test_build_recent_events_panel_requires_tuple() -> None:
    service = DashboardService()

    with pytest.raises(TypeError):
        service.build_recent_events_panel(
            events=[],  # type: ignore[arg-type]
        )


def test_build_recent_events_panel_rejects_invalid_event() -> None:
    service = DashboardService()

    with pytest.raises(TypeError):
        service.build_recent_events_panel(
            events=(
                object(),  # type: ignore[arg-type]
            ),
        )


def test_build_recent_events_panel_rejects_invalid_viewport() -> None:
    service = DashboardService()

    with pytest.raises(
        TypeError,
        match="viewport must be a PanelViewport",
    ):
        service.build_recent_events_panel(
            events=(),
            viewport="bad",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "limit",
    (
        True,
        1.5,
        "5",
    ),
)
def test_build_recent_events_panel_requires_integer_limit(
    limit,
) -> None:
    service = DashboardService()

    with pytest.raises(TypeError):
        service.build_recent_events_panel(
            events=(),
            limit=limit,
        )


# ---------------------------------------------------------------------------
# ACTIVE ALARMS
# ---------------------------------------------------------------------------


def test_build_active_alarms_panel() -> None:
    from datetime import datetime, timezone

    from app.noc.domain.node_alarm import (
        AlarmRecord,
        AlarmSeverity,
        AlarmState,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    older = AlarmRecord(
        alarm_id="alarm-001",
        alarm_type="NODE_HEALTH_DEGRADED",
        severity=AlarmSeverity.WARNING,
        state=AlarmState.ACTIVE,
        timestamp=datetime(
            2026,
            8,
            21,
            22,
            0,
            tzinfo=timezone.utc,
        ),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        title="Node health degraded to WARNING",
        description="Health degraded",
    )

    newer = AlarmRecord(
        alarm_id="alarm-002",
        alarm_type="NODE_HEALTH_DEGRADED",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=datetime(
            2026,
            8,
            21,
            22,
            30,
            tzinfo=timezone.utc,
        ),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        title="Node health degraded to CRITICAL",
        description="Health degraded",
    )

    panel = service.build_active_alarms_panel(
        alarms=(
            older,
            newer,
        )
    )

    assert panel.alarm_count == 2

    assert panel.alarms[0].alarm_id == (
        "alarm-002"
    )
    assert panel.alarms[0].severity == (
        "CRITICAL"
    )
    assert panel.alarms[0].state == (
        "ACTIVE"
    )
    assert panel.alarms[0].message == (
        "Node health degraded to CRITICAL"
    )

    assert panel.alarms[1].alarm_id == (
        "alarm-001"
    )


def test_build_active_alarms_panel_filters_resolved() -> None:
    from datetime import datetime, timedelta, timezone

    from app.noc.domain.node_alarm import (
        AlarmRecord,
        AlarmSeverity,
        AlarmState,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    raised = datetime(
        2026,
        8,
        21,
        22,
        0,
        tzinfo=timezone.utc,
    )

    active = AlarmRecord(
        alarm_id="alarm-001",
        alarm_type="NODE_HEALTH_DEGRADED",
        severity=AlarmSeverity.CRITICAL,
        state=AlarmState.ACTIVE,
        timestamp=raised,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        title="Node health degraded",
        description="Health degraded",
    )

    resolved = AlarmRecord(
        alarm_id="alarm-002",
        alarm_type="NODE_HEALTH_DEGRADED",
        severity=AlarmSeverity.WARNING,
        state=AlarmState.RESOLVED,
        timestamp=raised,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        title="Node health degraded",
        description="Health degraded",
        resolved_at=(
            raised + timedelta(seconds=10)
        ),
    )

    panel = service.build_active_alarms_panel(
        alarms=(
            active,
            resolved,
        )
    )

    assert panel.alarm_count == 1
    assert panel.alarms[0].alarm_id == (
        "alarm-001"
    )


def test_build_active_alarms_panel_accepts_acknowledged() -> None:
    from datetime import datetime, timedelta, timezone

    from app.noc.domain.node_alarm import (
        AlarmRecord,
        AlarmSeverity,
        AlarmState,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    raised = datetime(
        2026,
        8,
        21,
        22,
        0,
        tzinfo=timezone.utc,
    )

    alarm = AlarmRecord(
        alarm_id="alarm-001",
        alarm_type="NODE_HEALTH_DEGRADED",
        severity=AlarmSeverity.MAJOR,
        state=AlarmState.ACKNOWLEDGED,
        timestamp=raised,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        title="Node health degraded",
        description="Health degraded",
        acknowledged=True,
        acknowledged_by="operator",
        acknowledged_at=(
            raised + timedelta(seconds=5)
        ),
    )

    panel = service.build_active_alarms_panel(
        alarms=(alarm,)
    )

    assert panel.alarm_count == 1
    assert panel.alarms[0].state == (
        "ACKNOWLEDGED"
    )


def test_build_active_alarms_panel_limits_results() -> None:
    from datetime import datetime, timedelta, timezone

    from app.noc.domain.node_alarm import (
        AlarmRecord,
        AlarmSeverity,
        AlarmState,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    base = datetime(
        2026,
        8,
        21,
        22,
        0,
        tzinfo=timezone.utc,
    )

    alarms = tuple(
        AlarmRecord(
            alarm_id=f"alarm-{index}",
            alarm_type="NODE_HEALTH_DEGRADED",
            severity=AlarmSeverity.WARNING,
            state=AlarmState.ACTIVE,
            timestamp=(
                base + timedelta(seconds=index)
            ),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            title=f"Alarm {index}",
            description="Health degraded",
        )
        for index in range(6)
    )

    panel = service.build_active_alarms_panel(
        alarms=alarms,
        viewport=PanelViewport(
            offset=0,
            page_size=3,
        ),
    )

    assert panel.alarm_count == 3
    assert tuple(
        row.alarm_id
        for row in panel.alarms
    ) == (
        "alarm-5",
        "alarm-4",
        "alarm-3",
    )


def test_build_active_alarms_panel_accepts_empty() -> None:
    service = DashboardService()

    panel = service.build_active_alarms_panel(
        alarms=(),
    )

    assert panel.is_empty is True


def test_build_active_alarms_panel_requires_tuple() -> None:
    service = DashboardService()

    with pytest.raises(TypeError):
        service.build_active_alarms_panel(
            alarms=[],  # type: ignore[arg-type]
        )


def test_build_active_alarms_panel_rejects_invalid_alarm() -> None:
    service = DashboardService()

    with pytest.raises(TypeError):
        service.build_active_alarms_panel(
            alarms=(
                object(),  # type: ignore[arg-type]
            )
        )


def test_build_active_alarms_panel_rejects_invalid_viewport() -> None:
    service = DashboardService()

    with pytest.raises(
        TypeError,
        match="viewport must be a PanelViewport",
    ):
        service.build_active_alarms_panel(
            alarms=(),
            viewport="bad",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "limit",
    (
        True,
        1.5,
        "5",
    ),
)
def test_build_active_alarms_panel_requires_integer_limit(
    limit,
) -> None:
    service = DashboardService()

    with pytest.raises(TypeError):
        service.build_active_alarms_panel(
            alarms=(),
            limit=limit,
        )


def test_build_recent_events_panel_preserves_session_operational_context() -> None:
    from datetime import datetime, timezone

    from app.noc.domain.node_event import (
        EventRecord,
        EventSeverity,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    event = EventRecord(
        event_id="evt-session-001",
        event_type="SESSION_CONNECTED",
        severity=EventSeverity.INFO,
        timestamp=datetime(
            2026, 9, 1, 1, 30, 0,
            tzinfo=timezone.utc,
        ),
        source=NodeInstanceId("ejtv-01"),
        title="SRT reader connected on impact",
        description="Test session event",
        attributes={
            "session_id": "srt-test-001",
            "remote_address": "47.190.17.101:57045",
            "remote_ip": "47.190.17.101",
            "path": "impact",
            "protocol": "SRT",
            "role": "READER",
        },
    )

    panel = service.build_recent_events_panel(
        events=(event,),
    )

    assert panel.event_count == 1

    row = panel.events[0]

    assert row.remote_address == "47.190.17.101:57045"
    assert row.path == "impact"
    assert row.protocol == "SRT"
    assert row.role == "READER"


def test_build_active_alarms_panel_preserves_session_operational_context() -> None:
    from datetime import datetime, timezone

    from app.noc.domain.node_alarm import (
        AlarmRecord,
        AlarmSeverity,
        AlarmState,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    alarm = AlarmRecord(
        alarm_id="alm-session-001",
        alarm_type="RECONNECT_FLAPPING",
        severity=AlarmSeverity.MAJOR,
        state=AlarmState.ACTIVE,
        timestamp=datetime(
            2026, 9, 1, 1, 35, 0,
            tzinfo=timezone.utc,
        ),
        source=NodeInstanceId("ejtv-01"),
        title="Repeated reconnects detected",
        description="Test reconnect flapping alarm",
        attributes={
            "remote_ip": "47.190.17.101",
            "path": "impact",
            "protocol": "SRT",
            "role": "READER",
            "reconnect_count": "4",
        },
    )

    panel = service.build_active_alarms_panel(
        alarms=(alarm,),
    )

    assert panel.alarm_count == 1

    row = panel.alarms[0]

    assert row.remote_address == "47.190.17.101"
    assert row.path == "impact"
    assert row.protocol == "SRT"
    assert row.role == "READER"


def test_build_recent_events_panel_applies_viewport_offset() -> None:
    from datetime import datetime, timedelta, timezone

    from app.noc.domain.node_event import (
        EventRecord,
        EventSeverity,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    base = datetime(
        2026,
        9,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )

    source = NodeInstanceId("streaming-primary")

    events = tuple(
        EventRecord(
            event_id=f"event-{index}",
            event_type="TEST_EVENT",
            severity=EventSeverity.INFO,
            timestamp=base + timedelta(seconds=index),
            source=source,
            title=f"Event {index}",
            description=f"Event {index}",
        )
        for index in range(10)
    )

    panel = service.build_recent_events_panel(
        events=events,
        viewport=PanelViewport(
            offset=2,
            page_size=3,
        ),
    )

    assert tuple(
        row.event_id
        for row in panel.events
    ) == (
        "event-7",
        "event-6",
        "event-5",
    )
    assert panel.total_items == 10


def test_build_recent_events_panel_without_viewport_returns_all() -> None:
    from datetime import datetime, timedelta, timezone

    from app.noc.domain.node_event import (
        EventRecord,
        EventSeverity,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    base = datetime(
        2026,
        9,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )

    source = NodeInstanceId("streaming-primary")

    events = tuple(
        EventRecord(
            event_id=f"event-{index}",
            event_type="TEST_EVENT",
            severity=EventSeverity.INFO,
            timestamp=base + timedelta(seconds=index),
            source=source,
            title=f"Event {index}",
            description=f"Event {index}",
        )
        for index in range(8)
    )

    panel = service.build_recent_events_panel(
        events=events,
    )

    assert panel.event_count == 8


def test_build_active_alarms_panel_applies_viewport_offset() -> None:
    from datetime import datetime, timedelta, timezone

    from app.noc.domain.node_alarm import (
        AlarmRecord,
        AlarmSeverity,
        AlarmState,
    )
    from app.noc.domain.node_instance import NodeInstanceId

    service = DashboardService()

    base = datetime(
        2026,
        9,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )

    source = NodeInstanceId("streaming-primary")

    alarms = tuple(
        AlarmRecord(
            alarm_id=f"alarm-{index}",
            alarm_type="TEST_ALARM",
            severity=AlarmSeverity.WARNING,
            state=AlarmState.ACTIVE,
            timestamp=base + timedelta(seconds=index),
            source=source,
            title=f"Alarm {index}",
            description=f"Alarm {index}",
        )
        for index in range(8)
    )

    panel = service.build_active_alarms_panel(
        alarms=alarms,
        viewport=PanelViewport(
            offset=1,
            page_size=3,
        ),
    )

    assert tuple(
        row.alarm_id
        for row in panel.alarms
    ) == (
        "alarm-6",
        "alarm-5",
        "alarm-4",
    )
    assert panel.total_items == 8


def test_build_active_connections_panel_applies_viewport() -> None:
    from unittest.mock import Mock

    service = DashboardService()

    sessions = []

    for index in range(10):
        session = Mock()

        session.session_id = f"session-{index}"
        session.remote_address = f"192.0.2.{index}:9000"
        session.location_label = "Costa Rica"
        session.country_code = "CR"
        session.asn = 12345
        session.provider = "Example ISP"

        session.protocol.value = "SRT"
        session.path = f"path-{index}"
        session.role.value = "READER"

        session.effective_bitrate_mbps = 5.0
        session.duration_seconds.return_value = 30.0
        session.username = None

        sessions.append(session)

    measurement = Mock()
    measurement.sessions = tuple(sessions)
    measurement.captured_at = Mock()

    panel = service.build_active_connections_panel(
        measurement=measurement,
        viewport=PanelViewport(
            offset=3,
            page_size=4,
        ),
    )

    assert tuple(
        row.session_id
        for row in panel.connections
    ) == (
        "session-3",
        "session-4",
        "session-5",
        "session-6",
    )
    assert panel.total_items == 10


def test_build_platform_health_panel_from_domain_health() -> None:
    """Debe proyectar PlatformHealth sin recalcular salud."""

    from app.domain.sessions import SessionProtocol
    from app.domain.streaming.aggregation import (
        HealthPopulation,
        PlatformHealth,
        ProtocolHealth,
        ServiceHealth,
    )
    from app.domain.streaming.health import HealthStatus

    service = DashboardService()

    captured_at = datetime(
        2026,
        9,
        9,
        20,
        18,
        tzinfo=timezone.utc,
    )

    population = HealthPopulation(
        healthy_count=2,
        degraded_count=1,
        critical_count=1,
        unknown_count=1,
    )

    protocol_health = ProtocolHealth(
        service_id="ejtv",
        protocol=SessionProtocol.SRT,
        population=population,
        reader_count=5,
        publisher_count=0,
        unknown_role_count=0,
        status=HealthStatus.DEGRADED,
        worst_observed_status=HealthStatus.CRITICAL,
        message="SRT health test",
    )

    service_health = ServiceHealth(
        service_id="ejtv",
        protocols=(protocol_health,),
        population=population,
        status=HealthStatus.DEGRADED,
        worst_observed_status=HealthStatus.CRITICAL,
        message="Service health test",
    )

    platform_health = PlatformHealth(
        captured_at=captured_at,
        services=(service_health,),
        population=population,
        status=HealthStatus.DEGRADED,
        worst_observed_status=HealthStatus.CRITICAL,
        message="Platform health test",
    )

    panel = service.build_platform_health_panel(
        platform_health=platform_health,
    )

    assert panel.status == "DEGRADED"
    assert panel.worst_status == "CRITICAL"
    assert panel.healthy_count == 2
    assert panel.degraded_count == 1
    assert panel.critical_count == 1
    assert panel.unknown_count == 1
    assert panel.evidence_coverage == 0.8
    assert panel.affected_fraction == 0.5
    assert panel.service_count == 1
    assert panel.captured_at == captured_at


def test_build_dashboard_from_measurement_transports_platform_health() -> None:
    """Debe proyectar PlatformHealth y transportarlo en DashboardData."""

    from app.domain.streaming.aggregation import (
        HealthPopulation,
        PlatformHealth,
    )
    from app.domain.streaming.health import HealthStatus

    service = DashboardService()

    captured_at = datetime(
        2026,
        9,
        9,
        21,
        0,
        tzinfo=timezone.utc,
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

    dashboard = service.build_dashboard_from_measurement(
        hostname="ejtv-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        measurement=measurement,
        platform_health=platform_health,
    )

    assert dashboard.platform_health is not None
    assert dashboard.platform_health.status == "UNKNOWN"
    assert dashboard.platform_health.worst_status == "UNKNOWN"
    assert dashboard.platform_health.healthy_count == 0
    assert dashboard.platform_health.degraded_count == 0
    assert dashboard.platform_health.critical_count == 0
    assert dashboard.platform_health.unknown_count == 0
    assert dashboard.platform_health.evidence_coverage is None
    assert dashboard.platform_health.affected_fraction is None
    assert dashboard.platform_health.service_count == 0
    assert dashboard.platform_health.captured_at == captured_at


def test_build_dashboard_accepts_platform_health_independent_capture_time() -> None:
    """Platform Health conserva el instante de su SessionSnapshot fuente."""

    from datetime import timedelta

    from app.domain.streaming.aggregation import (
        HealthPopulation,
        PlatformHealth,
    )
    from app.domain.streaming.health import HealthStatus

    service = DashboardService()

    captured_at = datetime(
        2026,
        9,
        9,
        21,
        30,
        41,
        709130,
        tzinfo=timezone.utc,
    )

    platform_captured_at = (
        captured_at
        + timedelta(microseconds=5577)
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
        captured_at=platform_captured_at,
        services=(),
        population=HealthPopulation(
            healthy_count=0,
            degraded_count=0,
            critical_count=0,
            unknown_count=0,
        ),
        status=HealthStatus.UNKNOWN,
        worst_observed_status=HealthStatus.UNKNOWN,
        message="No active multimedia sessions were observed.",
    )

    dashboard = service.build_dashboard_from_measurement(
        hostname="ejtv-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=snapshot,
        measurement=measurement,
        platform_health=platform_health,
    )

    assert dashboard.platform_health is not None
    assert (
        dashboard.platform_health.captured_at
        == platform_captured_at
    )

def test_build_active_connections_panel_projects_rtmp_unknown_health() -> None:
    """Debe preservar UNKNOWN de evidencia RTMP especializada."""

    from app.domain.streaming import HealthStatus, RTMPConnectionHealth

    captured_at = datetime(
        2026,
        9,
        10,
        18,
        0,
        tzinfo=timezone.utc,
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

    measurement = SessionMeasurement(
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
        message="Insufficient temporal evidence for RTMP connection.",
    )

    panel = DashboardService().build_active_connections_panel(
        measurement=measurement,
        rtmp_connections=(rtmp_health,),
    )

    assert panel.connection_count == 1
    assert panel.connections[0].health == "UNKNOWN"

def test_build_active_connections_panel_rejects_ambiguous_rtmp_health() -> None:
    """No debe elegir arbitrariamente entre evidencias RTMP duplicadas."""

    from app.domain.streaming import HealthStatus, RTMPConnectionHealth

    captured_at = datetime(
        2026,
        9,
        10,
        18,
        5,
        tzinfo=timezone.utc,
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

    measurement = SessionMeasurement(
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

    first = RTMPConnectionHealth(
        connection_id="rtmp-reader-001",
        path_name="impact",
        state="read",
        effective_delta_bytes=None,
        effective_bitrate_mbps=None,
        outbound_frames_discarded=None,
        status=HealthStatus.UNKNOWN,
        message="Insufficient temporal evidence.",
    )

    second = RTMPConnectionHealth(
        connection_id="rtmp-reader-001",
        path_name="impact",
        state="read",
        effective_delta_bytes=500000,
        effective_bitrate_mbps=0.8,
        outbound_frames_discarded=None,
        status=HealthStatus.HEALTHY,
        message="RTMP connection is healthy.",
    )

    panel = DashboardService().build_active_connections_panel(
        measurement=measurement,
        rtmp_connections=(first, second),
    )

    assert panel.connection_count == 1
    assert panel.connections[0].health is None
