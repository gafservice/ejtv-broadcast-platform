from __future__ import annotations

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingPathMeasurement,
)
from app.domain.streaming.models import MediaPathStatus
from app.services.source_transport_health_evaluator import (
    SourceTransportHealthEvaluator,
)


def measurement(
    *,
    path_name: str = "impact",
    status: MediaPathStatus = MediaPathStatus.ACTIVE,
    previous_status: MediaPathStatus | None = MediaPathStatus.ACTIVE,
    inbound_delta_bytes: int | None = 1_000_000,
    inbound_bitrate_bps: float | None = 1_600_000.0,
    quality: MeasurementQuality = MeasurementQuality.AVAILABLE,
) -> StreamingPathMeasurement:
    return StreamingPathMeasurement(
        name=path_name,
        status=status,
        previous_status=previous_status,
        reader_count=0,
        reader_delta=0 if inbound_delta_bytes is not None else None,
        inbound_delta_bytes=inbound_delta_bytes,
        outbound_delta_bytes=0 if inbound_delta_bytes is not None else None,
        inbound_bitrate_bps=inbound_bitrate_bps,
        outbound_bitrate_bps=0.0 if inbound_bitrate_bps is not None else None,
        state_changed=(
            previous_status is not None
            and status is not previous_status
        ),
        quality=quality,
    )


def test_positive_source_receive_traffic_is_healthy() -> None:
    evaluator = SourceTransportHealthEvaluator()

    result = evaluator.evaluate(
        service_id="impact",
        source_type="srtSource",
        measurement=measurement(),
    )

    assert result.service_id == "impact"
    assert result.path_name == "impact"
    assert result.source_type == "srtSource"
    assert result.status is HealthStatus.HEALTHY


def test_zero_source_receive_traffic_is_degraded() -> None:
    evaluator = SourceTransportHealthEvaluator()

    result = evaluator.evaluate(
        service_id="impact",
        source_type="srtSource",
        measurement=measurement(
            inbound_delta_bytes=0,
            inbound_bitrate_bps=0.0,
        ),
    )

    assert result.status is HealthStatus.DEGRADED


def test_missing_temporal_measurement_is_unknown() -> None:
    evaluator = SourceTransportHealthEvaluator()

    result = evaluator.evaluate(
        service_id="impact",
        source_type="srtSource",
        measurement=measurement(
            previous_status=None,
            inbound_delta_bytes=None,
            inbound_bitrate_bps=None,
            quality=MeasurementQuality.NOT_AVAILABLE,
        ),
    )

    assert result.status is HealthStatus.UNKNOWN


def test_invalid_temporal_measurement_is_unknown() -> None:
    evaluator = SourceTransportHealthEvaluator()

    result = evaluator.evaluate(
        service_id="impact",
        source_type="srtSource",
        measurement=measurement(
            inbound_delta_bytes=1_000_000,
            inbound_bitrate_bps=1_600_000.0,
            quality=MeasurementQuality.INVALID,
        ),
    )

    assert result.status is HealthStatus.UNKNOWN



def test_offline_source_is_critical() -> None:
    evaluator = SourceTransportHealthEvaluator()

    result = evaluator.evaluate(
        service_id="impact",
        source_type="srtSource",
        measurement=measurement(
            status=MediaPathStatus.OFFLINE,
            previous_status=MediaPathStatus.ACTIVE,
            inbound_delta_bytes=0,
            inbound_bitrate_bps=0.0,
        ),
    )

    assert result.status is HealthStatus.CRITICAL


def test_no_source_is_critical() -> None:
    evaluator = SourceTransportHealthEvaluator()

    result = evaluator.evaluate(
        service_id="impact",
        source_type="srtSource",
        measurement=measurement(
            status=MediaPathStatus.NO_SOURCE,
            previous_status=MediaPathStatus.ACTIVE,
            inbound_delta_bytes=0,
            inbound_bitrate_bps=0.0,
        ),
    )

    assert result.status is HealthStatus.CRITICAL


def test_offline_source_dominates_invalid_measurement() -> None:
    evaluator = SourceTransportHealthEvaluator()

    result = evaluator.evaluate(
        service_id="impact",
        source_type="srtSource",
        measurement=measurement(
            status=MediaPathStatus.OFFLINE,
            inbound_delta_bytes=None,
            inbound_bitrate_bps=None,
            quality=MeasurementQuality.INVALID,
        ),
    )

    assert result.status is HealthStatus.CRITICAL


def test_no_source_dominates_invalid_measurement() -> None:
    evaluator = SourceTransportHealthEvaluator()

    result = evaluator.evaluate(
        service_id="impact",
        source_type="srtSource",
        measurement=measurement(
            status=MediaPathStatus.NO_SOURCE,
            inbound_delta_bytes=None,
            inbound_bitrate_bps=None,
            quality=MeasurementQuality.INVALID,
        ),
    )

    assert result.status is HealthStatus.CRITICAL


def test_non_measurement_input_is_rejected() -> None:
    evaluator = SourceTransportHealthEvaluator()

    try:
        evaluator.evaluate(
            service_id="impact",
            source_type="srtSource",
            measurement=object(),  # type: ignore[arg-type]
        )
    except TypeError as exc:
        assert (
            str(exc)
            == "measurement must be a StreamingPathMeasurement"
        )
    else:
        raise AssertionError("TypeError was not raised")



def test_evaluator_is_protocol_agnostic() -> None:
    evaluator = SourceTransportHealthEvaluator()

    result = evaluator.evaluate(
        service_id="future-service",
        source_type="futureSource",
        measurement=measurement(
            path_name="future-path",
        ),
    )

    assert result.service_id == "future-service"
    assert result.path_name == "future-path"
    assert result.source_type == "futureSource"
    assert result.status is HealthStatus.HEALTHY
