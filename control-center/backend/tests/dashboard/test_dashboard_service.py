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
