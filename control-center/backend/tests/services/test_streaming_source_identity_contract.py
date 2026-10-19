"""Functional contracts for publisher identity changes in StreamingService."""

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


def make_snapshot(
    *,
    seconds: int,
    source_id: str | None,
    inbound_bytes: int,
    outbound_bytes: int = 0,
    has_source: bool = True,
) -> MediaMTXSnapshot:
    source = (
        MediaSource(
            source_type="srtConn",
            source_id=source_id,
        )
        if has_source
        else None
    )

    active = source is not None

    path = MediaPath(
        name="impact",
        configuration_name="impact",
        status=(
            MediaPathStatus.ACTIVE
            if active
            else MediaPathStatus.NO_SOURCE
        ),
        ready=active,
        available=active,
        online=active,
        source=source,
        inbound_bytes=inbound_bytes,
        outbound_bytes=outbound_bytes,
    )

    return MediaMTXSnapshot(
        captured_at=T0 + timedelta(seconds=seconds),
        paths=(path,),
        reported_item_count=1,
        reported_page_count=1,
    )


def test_changed_publisher_id_discards_cross_source_delta():
    service = StreamingService()

    previous = make_snapshot(
        seconds=0,
        source_id="publisher-A",
        inbound_bytes=1_000_000,
    )

    current = make_snapshot(
        seconds=1,
        source_id="publisher-B",
        inbound_bytes=2_000_000,
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("impact")

    assert path is not None
    assert path.quality is MeasurementQuality.NOT_AVAILABLE
    assert path.inbound_delta_bytes is None
    assert path.inbound_bitrate_bps is None


def test_source_disappearance_discards_cross_source_delta():
    service = StreamingService()

    previous = make_snapshot(
        seconds=0,
        source_id="publisher-A",
        inbound_bytes=1_000_000,
    )

    current = make_snapshot(
        seconds=1,
        source_id=None,
        inbound_bytes=1_500_000,
        has_source=False,
    )

    measurement = service.compare(previous, current)
    path = measurement.get_path("impact")

    assert path is not None
    assert path.quality is MeasurementQuality.NOT_AVAILABLE
    assert path.inbound_delta_bytes is None
    assert path.inbound_bitrate_bps is None


def test_replacement_publisher_establishes_new_baseline():
    service = StreamingService()

    first = make_snapshot(
        seconds=0,
        source_id="publisher-A",
        inbound_bytes=1_000_000,
    )

    replacement = make_snapshot(
        seconds=1,
        source_id="publisher-B",
        inbound_bytes=2_000_000,
    )

    next_capture = make_snapshot(
        seconds=2,
        source_id="publisher-B",
        inbound_bytes=2_750_000,
    )

    transition = service.compare(first, replacement)
    transition_path = transition.get_path("impact")

    assert transition_path is not None
    assert transition_path.quality is MeasurementQuality.NOT_AVAILABLE
    assert transition_path.inbound_bitrate_bps is None

    resumed = service.compare(replacement, next_capture)
    resumed_path = resumed.get_path("impact")

    assert resumed_path is not None
    assert resumed_path.quality is MeasurementQuality.AVAILABLE
    assert resumed_path.inbound_delta_bytes == 750_000
    assert resumed_path.inbound_bitrate_bps == 6_000_000.0
