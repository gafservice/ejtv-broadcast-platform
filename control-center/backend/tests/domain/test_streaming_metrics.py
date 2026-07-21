"""Pruebas de los modelos de métricas multimedia derivadas."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.streaming import (
    MeasurementQuality,
    MediaPathStatus,
    StreamingMeasurement,
    StreamingPathMeasurement,
)


def build_path_measurement(
    *,
    name: str = "enlace",
    status: MediaPathStatus = MediaPathStatus.ACTIVE,
    previous_status: MediaPathStatus | None = MediaPathStatus.ACTIVE,
    reader_count: int = 2,
    reader_delta: int | None = 1,
    inbound_delta_bytes: int | None = 1_250_000,
    outbound_delta_bytes: int | None = 625_000,
    inbound_bitrate_bps: float | None = 1_000_000.0,
    outbound_bitrate_bps: float | None = 500_000.0,
    state_changed: bool = False,
    quality: MeasurementQuality = MeasurementQuality.AVAILABLE,
) -> StreamingPathMeasurement:
    """Construye una medición válida para pruebas."""

    return StreamingPathMeasurement(
        name=name,
        status=status,
        previous_status=previous_status,
        reader_count=reader_count,
        reader_delta=reader_delta,
        inbound_delta_bytes=inbound_delta_bytes,
        outbound_delta_bytes=outbound_delta_bytes,
        inbound_bitrate_bps=inbound_bitrate_bps,
        outbound_bitrate_bps=outbound_bitrate_bps,
        state_changed=state_changed,
        quality=quality,
    )


def test_path_measurement_exposes_derived_values() -> None:
    measurement = build_path_measurement()

    assert measurement.inbound_bitrate_mbps == 1.0
    assert measurement.outbound_bitrate_mbps == 0.5
    assert measurement.readers_connected == 1
    assert measurement.readers_disconnected == 0


def test_path_measurement_detects_disconnected_readers() -> None:
    measurement = build_path_measurement(
        reader_count=1,
        reader_delta=-2,
    )

    assert measurement.readers_connected == 0
    assert measurement.readers_disconnected == 2


def test_path_measurement_accepts_not_available_values() -> None:
    measurement = build_path_measurement(
        previous_status=None,
        reader_delta=None,
        inbound_delta_bytes=None,
        outbound_delta_bytes=None,
        inbound_bitrate_bps=None,
        outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    assert measurement.inbound_bitrate_mbps is None
    assert measurement.outbound_bitrate_mbps is None
    assert measurement.readers_connected == 0
    assert measurement.readers_disconnected == 0


def test_available_path_requires_derived_values() -> None:
    with pytest.raises(ValueError):
        build_path_measurement(
            inbound_bitrate_bps=None,
            quality=MeasurementQuality.AVAILABLE,
        )


def test_path_rejects_negative_counters() -> None:
    with pytest.raises(ValueError):
        build_path_measurement(
            inbound_delta_bytes=-1,
        )


def test_path_measurement_is_immutable() -> None:
    measurement = build_path_measurement()

    with pytest.raises(FrozenInstanceError):
        measurement.reader_count = 5  # type: ignore[misc]


def test_streaming_measurement_exposes_global_totals() -> None:
    captured_at = datetime.now(UTC)
    previous_captured_at = captured_at - timedelta(seconds=10)

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=previous_captured_at,
        interval_seconds=10.0,
        paths=(
            build_path_measurement(
                name="enlace",
                reader_count=2,
                state_changed=False,
            ),
            build_path_measurement(
                name="canal-2",
                reader_count=3,
                status=MediaPathStatus.OFFLINE,
                previous_status=MediaPathStatus.ACTIVE,
                state_changed=True,
            ),
        ),
        total_inbound_bitrate_bps=2_000_000.0,
        total_outbound_bitrate_bps=1_000_000.0,
        quality=MeasurementQuality.AVAILABLE,
    )

    assert measurement.path_count == 2
    assert measurement.valid_path_count == 2
    assert measurement.state_change_count == 1
    assert measurement.total_reader_count == 5
    assert measurement.total_inbound_bitrate_mbps == 2.0
    assert measurement.total_outbound_bitrate_mbps == 1.0
    assert measurement.get_path("enlace") is not None
    assert measurement.get_path("missing") is None


def test_first_measurement_can_be_not_available() -> None:
    captured_at = datetime.now(UTC)

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(
            build_path_measurement(
                previous_status=None,
                reader_delta=None,
                inbound_delta_bytes=None,
                outbound_delta_bytes=None,
                inbound_bitrate_bps=None,
                outbound_bitrate_bps=None,
                quality=MeasurementQuality.NOT_AVAILABLE,
            ),
        ),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    assert measurement.path_count == 1
    assert measurement.valid_path_count == 0
    assert measurement.total_inbound_bitrate_mbps is None


def test_available_measurement_requires_previous_snapshot() -> None:
    with pytest.raises(ValueError):
        StreamingMeasurement(
            captured_at=datetime.now(UTC),
            previous_captured_at=None,
            interval_seconds=10.0,
            paths=(),
            total_inbound_bitrate_bps=0.0,
            total_outbound_bitrate_bps=0.0,
            quality=MeasurementQuality.AVAILABLE,
        )


def test_measurement_rejects_non_positive_interval() -> None:
    captured_at = datetime.now(UTC)

    with pytest.raises(ValueError):
        StreamingMeasurement(
            captured_at=captured_at,
            previous_captured_at=captured_at,
            interval_seconds=0.0,
            paths=(),
            total_inbound_bitrate_bps=0.0,
            total_outbound_bitrate_bps=0.0,
            quality=MeasurementQuality.AVAILABLE,
        )


def test_measurement_requires_timezone() -> None:
    with pytest.raises(ValueError):
        StreamingMeasurement(
            captured_at=datetime.now(),
            previous_captured_at=None,
            interval_seconds=None,
            paths=(),
            total_inbound_bitrate_bps=None,
            total_outbound_bitrate_bps=None,
            quality=MeasurementQuality.NOT_AVAILABLE,
        )
