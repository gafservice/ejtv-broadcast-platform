"""Source continuity contracts for MediaMTX bitrate measurements."""

from datetime import UTC, datetime, timedelta

from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
)
from app.services import StreamingService


T0 = datetime(2026, 10, 19, 18, 0, tzinfo=UTC)


def snapshot(
    *,
    seconds: int,
    inbound_bytes: int,
    ready_time: datetime | None,
) -> MediaMTXSnapshot:
    path = MediaPath(
        name="impact",
        configuration_name="impact",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        ready_time=ready_time,
        source=MediaSource(
            source_type="srtConn",
            source_id="publisher-A",
        ),
        inbound_bytes=inbound_bytes,
        outbound_bytes=0,
    )

    return MediaMTXSnapshot(
        captured_at=T0 + timedelta(seconds=seconds),
        paths=(path,),
        reported_item_count=1,
        reported_page_count=1,
    )


def test_same_identity_and_ready_time_remains_available():
    service = StreamingService()

    ready_time = T0 - timedelta(seconds=30)

    previous = snapshot(
        seconds=0,
        inbound_bytes=1_000_000,
        ready_time=ready_time,
    )

    current = snapshot(
        seconds=1,
        inbound_bytes=1_750_000,
        ready_time=ready_time,
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("impact")

    assert path is not None
    assert path.quality is MeasurementQuality.AVAILABLE
    assert path.inbound_bitrate_bps == 6_000_000.0


def test_changed_ready_time_discards_previous_session_delta():
    service = StreamingService()

    previous = snapshot(
        seconds=0,
        inbound_bytes=1_000_000,
        ready_time=T0 - timedelta(seconds=30),
    )

    current = snapshot(
        seconds=1,
        inbound_bytes=1_750_000,
        ready_time=T0,
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("impact")

    assert path is not None
    assert path.quality is MeasurementQuality.NOT_AVAILABLE
    assert path.inbound_delta_bytes is None
    assert path.inbound_bitrate_bps is None


def test_missing_ready_time_preserves_existing_bitrate_behavior():
    service = StreamingService()

    previous = snapshot(
        seconds=0,
        inbound_bytes=1_000_000,
        ready_time=None,
    )

    current = snapshot(
        seconds=1,
        inbound_bytes=1_750_000,
        ready_time=None,
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("impact")

    assert path is not None
    assert path.quality is MeasurementQuality.AVAILABLE
    assert path.inbound_bitrate_bps == 6_000_000.0
