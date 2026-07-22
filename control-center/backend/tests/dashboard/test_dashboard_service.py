"""Pruebas del DashboardService."""

from datetime import datetime, timezone

import pytest

from app.dashboard.services.dashboard_service import DashboardService
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
    StreamingMeasurement,
    StreamingPathMeasurement,
)


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
    assert path.source == "udpSource"


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
