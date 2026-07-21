"""Pruebas unitarias de StreamingService."""

from datetime import UTC, datetime, timedelta

from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaReader,
)
from app.services import StreamingService


def build_path(
    *,
    name: str = "enlace",
    status: MediaPathStatus = MediaPathStatus.ACTIVE,
    readers: int = 1,
    inbound_bytes: int = 0,
    outbound_bytes: int = 0,
) -> MediaPath:
    """Construye un path multimedia para pruebas."""

    return MediaPath(
        name=name,
        configuration_name=name,
        status=status,
        ready=status is MediaPathStatus.ACTIVE,
        available=status is MediaPathStatus.ACTIVE,
        online=status is MediaPathStatus.ACTIVE,
        readers=tuple(
            MediaReader(
                reader_type="srtConn",
                reader_id=f"reader-{index}",
            )
            for index in range(readers)
        ),
        inbound_bytes=inbound_bytes,
        outbound_bytes=outbound_bytes,
    )


def build_snapshot(
    *,
    captured_at: datetime,
    paths: tuple[MediaPath, ...],
) -> MediaMTXSnapshot:
    """Construye un snapshot multimedia para pruebas."""

    return MediaMTXSnapshot(
        captured_at=captured_at,
        paths=paths,
        reported_item_count=len(paths),
        reported_page_count=1 if paths else 0,
    )


def test_first_snapshot_is_not_available() -> None:
    service = StreamingService()
    captured_at = datetime.now(UTC)

    current = build_snapshot(
        captured_at=captured_at,
        paths=(
            build_path(
                inbound_bytes=1_000,
                outbound_bytes=2_000,
            ),
        ),
    )

    measurement = service.compare(
        previous=None,
        current=current,
    )

    assert measurement.quality is MeasurementQuality.NOT_AVAILABLE
    assert measurement.previous_captured_at is None
    assert measurement.interval_seconds is None
    assert measurement.path_count == 1

    path = measurement.get_path("enlace")

    assert path is not None
    assert path.quality is MeasurementQuality.NOT_AVAILABLE
    assert path.inbound_bitrate_bps is None
    assert path.outbound_bitrate_bps is None


def test_service_calculates_bitrate() -> None:
    service = StreamingService()
    previous_time = datetime.now(UTC)
    current_time = previous_time + timedelta(seconds=10)

    previous = build_snapshot(
        captured_at=previous_time,
        paths=(
            build_path(
                inbound_bytes=1_000_000,
                outbound_bytes=2_000_000,
            ),
        ),
    )

    current = build_snapshot(
        captured_at=current_time,
        paths=(
            build_path(
                inbound_bytes=2_250_000,
                outbound_bytes=2_625_000,
            ),
        ),
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("enlace")

    assert measurement.quality is MeasurementQuality.AVAILABLE
    assert measurement.interval_seconds == 10.0
    assert measurement.total_inbound_bitrate_bps == 1_000_000.0
    assert measurement.total_outbound_bitrate_bps == 500_000.0

    assert path is not None
    assert path.inbound_delta_bytes == 1_250_000
    assert path.outbound_delta_bytes == 625_000
    assert path.inbound_bitrate_bps == 1_000_000.0
    assert path.outbound_bitrate_bps == 500_000.0


def test_zero_traffic_is_a_valid_measurement() -> None:
    service = StreamingService()
    previous_time = datetime.now(UTC)
    current_time = previous_time + timedelta(seconds=5)

    previous = build_snapshot(
        captured_at=previous_time,
        paths=(
            build_path(
                inbound_bytes=5_000,
                outbound_bytes=8_000,
            ),
        ),
    )

    current = build_snapshot(
        captured_at=current_time,
        paths=(
            build_path(
                inbound_bytes=5_000,
                outbound_bytes=8_000,
            ),
        ),
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("enlace")

    assert measurement.quality is MeasurementQuality.AVAILABLE
    assert measurement.total_inbound_bitrate_bps == 0.0
    assert measurement.total_outbound_bitrate_bps == 0.0

    assert path is not None
    assert path.inbound_bitrate_bps == 0.0
    assert path.outbound_bitrate_bps == 0.0


def test_service_calculates_reader_delta() -> None:
    service = StreamingService()
    previous_time = datetime.now(UTC)
    current_time = previous_time + timedelta(seconds=5)

    previous = build_snapshot(
        captured_at=previous_time,
        paths=(
            build_path(
                readers=1,
                inbound_bytes=1_000,
                outbound_bytes=1_000,
            ),
        ),
    )

    current = build_snapshot(
        captured_at=current_time,
        paths=(
            build_path(
                readers=3,
                inbound_bytes=2_000,
                outbound_bytes=3_000,
            ),
        ),
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("enlace")

    assert path is not None
    assert path.reader_count == 3
    assert path.reader_delta == 2
    assert path.readers_connected == 2
    assert path.readers_disconnected == 0


def test_service_detects_state_change() -> None:
    service = StreamingService()
    previous_time = datetime.now(UTC)
    current_time = previous_time + timedelta(seconds=5)

    previous = build_snapshot(
        captured_at=previous_time,
        paths=(
            build_path(
                status=MediaPathStatus.ACTIVE,
                inbound_bytes=1_000,
                outbound_bytes=1_000,
            ),
        ),
    )

    current = build_snapshot(
        captured_at=current_time,
        paths=(
            build_path(
                status=MediaPathStatus.OFFLINE,
                inbound_bytes=1_000,
                outbound_bytes=1_000,
            ),
        ),
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("enlace")

    assert path is not None
    assert path.previous_status is MediaPathStatus.ACTIVE
    assert path.status is MediaPathStatus.OFFLINE
    assert path.state_changed is True
    assert measurement.state_change_count == 1


def test_new_path_is_not_available() -> None:
    service = StreamingService()
    previous_time = datetime.now(UTC)
    current_time = previous_time + timedelta(seconds=5)

    previous = build_snapshot(
        captured_at=previous_time,
        paths=(),
    )

    current = build_snapshot(
        captured_at=current_time,
        paths=(
            build_path(
                name="nuevo",
                inbound_bytes=50_000,
                outbound_bytes=10_000,
            ),
        ),
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("nuevo")

    assert measurement.quality is MeasurementQuality.NOT_AVAILABLE
    assert path is not None
    assert path.previous_status is None
    assert path.quality is MeasurementQuality.NOT_AVAILABLE
    assert path.inbound_bitrate_bps is None


def test_counter_reset_is_invalid() -> None:
    service = StreamingService()
    previous_time = datetime.now(UTC)
    current_time = previous_time + timedelta(seconds=5)

    previous = build_snapshot(
        captured_at=previous_time,
        paths=(
            build_path(
                inbound_bytes=100_000,
                outbound_bytes=200_000,
            ),
        ),
    )

    current = build_snapshot(
        captured_at=current_time,
        paths=(
            build_path(
                inbound_bytes=500,
                outbound_bytes=700,
            ),
        ),
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("enlace")

    assert measurement.quality is MeasurementQuality.INVALID
    assert measurement.total_inbound_bitrate_bps is None
    assert measurement.total_outbound_bitrate_bps is None

    assert path is not None
    assert path.quality is MeasurementQuality.INVALID
    assert path.inbound_bitrate_bps is None
    assert path.outbound_bitrate_bps is None


def test_non_positive_interval_is_invalid() -> None:
    service = StreamingService()
    captured_at = datetime.now(UTC)

    previous = build_snapshot(
        captured_at=captured_at,
        paths=(build_path(),),
    )

    current = build_snapshot(
        captured_at=captured_at,
        paths=(build_path(),),
    )

    measurement = service.compare(previous, current)

    assert measurement.quality is MeasurementQuality.INVALID
    assert measurement.interval_seconds is None
    assert measurement.total_inbound_bitrate_bps is None


def test_global_quality_is_invalid_when_one_path_is_invalid() -> None:
    service = StreamingService()
    previous_time = datetime.now(UTC)
    current_time = previous_time + timedelta(seconds=10)

    previous = build_snapshot(
        captured_at=previous_time,
        paths=(
            build_path(
                name="estable",
                inbound_bytes=1_000,
                outbound_bytes=1_000,
            ),
            build_path(
                name="reiniciado",
                inbound_bytes=10_000,
                outbound_bytes=10_000,
            ),
        ),
    )

    current = build_snapshot(
        captured_at=current_time,
        paths=(
            build_path(
                name="estable",
                inbound_bytes=2_000,
                outbound_bytes=2_000,
            ),
            build_path(
                name="reiniciado",
                inbound_bytes=100,
                outbound_bytes=100,
            ),
        ),
    )

    measurement = service.compare(previous, current)

    assert measurement.quality is MeasurementQuality.INVALID
    assert measurement.valid_path_count == 1
    assert measurement.total_inbound_bitrate_bps is None
    assert measurement.total_outbound_bitrate_bps is None
