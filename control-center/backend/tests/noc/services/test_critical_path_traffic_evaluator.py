from datetime import datetime, timezone

import pytest

from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingMeasurement,
    StreamingPathMeasurement,
)
from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaSource,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.services.critical_path_traffic_evaluator import (
    CriticalPathTrafficEvaluator,
    CriticalPathTrafficState,
)


NOW = datetime(2026, 8, 31, 8, 0, tzinfo=timezone.utc)


def make_path(
    name: str = "ejtv",
    *,
    active: bool = True,
    source: bool = True,
    ready: bool = True,
    available: bool = True,
    online: bool = True,
) -> MediaPath:
    return MediaPath(
        name=name,
        configuration_name=name,
        status=(
            MediaPathStatus.ACTIVE
            if active
            else MediaPathStatus.OFFLINE
        ),
        ready=ready,
        available=available,
        online=online,
        source=(
            MediaSource(source_type="mpegtsSource")
            if source
            else None
        ),
    )


def make_snapshot(
    *paths: MediaPath,
) -> MediaMTXSnapshot:
    return MediaMTXSnapshot(
        captured_at=NOW,
        paths=tuple(paths),
        reported_item_count=len(paths),
        reported_page_count=1,
    )


def make_path_measurement(
    name: str = "ejtv",
    *,
    bitrate: float | None = 4_500_000.0,
    quality: MeasurementQuality = MeasurementQuality.AVAILABLE,
) -> StreamingPathMeasurement:
    available = quality is MeasurementQuality.AVAILABLE

    return StreamingPathMeasurement(
        name=name,
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=0,
        reader_delta=0 if available else None,
        inbound_delta_bytes=100 if available else None,
        outbound_delta_bytes=0 if available else None,
        inbound_bitrate_bps=bitrate if available else None,
        outbound_bitrate_bps=0.0 if available else None,
        state_changed=False,
        quality=quality,
    )


def make_measurement(
    *paths: StreamingPathMeasurement,
) -> StreamingMeasurement:
    return StreamingMeasurement(
        captured_at=NOW,
        previous_captured_at=NOW,
        interval_seconds=1.0,
        paths=tuple(paths),
        total_inbound_bitrate_bps=(
            sum(
                path.inbound_bitrate_bps or 0.0
                for path in paths
            )
        ),
        total_outbound_bitrate_bps=(
            sum(
                path.outbound_bitrate_bps or 0.0
                for path in paths
            )
        ),
        quality=MeasurementQuality.AVAILABLE,
    )


def policy(
    path: str = "ejtv",
    *,
    enabled: bool = True,
) -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path=path,
        enabled=enabled,
    )


def test_positive_inbound_traffic_is_healthy() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    result = evaluator.evaluate(
        snapshot=make_snapshot(make_path()),
        measurement=make_measurement(
            make_path_measurement(
                bitrate=4_500_000.0
            )
        ),
        policies=(policy(),),
    )

    assert len(result) == 1
    assert result[0].state is CriticalPathTrafficState.HEALTHY
    assert result[0].measurement is not None
    assert (
        result[0].measurement.inbound_bitrate_bps
        == 4_500_000.0
    )


def test_zero_inbound_traffic_is_stalled() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    result = evaluator.evaluate(
        snapshot=make_snapshot(make_path()),
        measurement=make_measurement(
            make_path_measurement(bitrate=0.0)
        ),
        policies=(policy(),),
    )

    assert result[0].state is CriticalPathTrafficState.STALLED


@pytest.mark.parametrize(
    "path",
    (
        make_path(active=False),
        make_path(source=False),
        make_path(ready=False),
        make_path(available=False),
        make_path(online=False),
    ),
)
def test_non_operational_path_is_inactive(
    path: MediaPath,
) -> None:
    evaluator = CriticalPathTrafficEvaluator()

    result = evaluator.evaluate(
        snapshot=make_snapshot(path),
        measurement=make_measurement(
            make_path_measurement()
        ),
        policies=(policy(),),
    )

    assert result[0].state is CriticalPathTrafficState.INACTIVE


def test_missing_path_is_inactive() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    result = evaluator.evaluate(
        snapshot=make_snapshot(),
        measurement=make_measurement(),
        policies=(policy(),),
    )

    assert result[0].state is CriticalPathTrafficState.INACTIVE
    assert result[0].media_path is None


def test_missing_measurement_is_unknown() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    result = evaluator.evaluate(
        snapshot=make_snapshot(make_path()),
        measurement=make_measurement(),
        policies=(policy(),),
    )

    assert result[0].state is CriticalPathTrafficState.UNKNOWN


def test_unavailable_measurement_is_unknown() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    path_measurement = make_path_measurement(
        quality=MeasurementQuality.NOT_AVAILABLE
    )

    result = evaluator.evaluate(
        snapshot=make_snapshot(make_path()),
        measurement=StreamingMeasurement(
            captured_at=NOW,
            previous_captured_at=None,
            interval_seconds=None,
            paths=(path_measurement,),
            total_inbound_bitrate_bps=None,
            total_outbound_bitrate_bps=None,
            quality=MeasurementQuality.NOT_AVAILABLE,
        ),
        policies=(policy(),),
    )

    assert result[0].state is CriticalPathTrafficState.UNKNOWN


def test_disabled_policy_is_skipped() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    result = evaluator.evaluate(
        snapshot=make_snapshot(make_path()),
        measurement=make_measurement(
            make_path_measurement()
        ),
        policies=(policy(enabled=False),),
    )

    assert result == ()


def test_results_are_sorted_by_path() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    result = evaluator.evaluate(
        snapshot=make_snapshot(
            make_path("zeta"),
            make_path("alpha"),
        ),
        measurement=make_measurement(
            make_path_measurement("zeta"),
            make_path_measurement("alpha"),
        ),
        policies=(
            policy("zeta"),
            policy("alpha"),
        ),
    )

    assert tuple(
        item.policy.path for item in result
    ) == ("alpha", "zeta")


def test_duplicate_policy_paths_are_rejected() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    with pytest.raises(ValueError):
        evaluator.evaluate(
            snapshot=make_snapshot(make_path()),
            measurement=make_measurement(
                make_path_measurement()
            ),
            policies=(
                policy(),
                policy(),
            ),
        )


def test_invalid_snapshot_type_is_rejected() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    with pytest.raises(TypeError):
        evaluator.evaluate(
            snapshot=object(),  # type: ignore[arg-type]
            measurement=make_measurement(),
            policies=(policy(),),
        )


def test_invalid_measurement_type_is_rejected() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    with pytest.raises(TypeError):
        evaluator.evaluate(
            snapshot=make_snapshot(make_path()),
            measurement=object(),  # type: ignore[arg-type]
            policies=(policy(),),
        )


def test_invalid_policies_container_is_rejected() -> None:
    evaluator = CriticalPathTrafficEvaluator()

    with pytest.raises(TypeError):
        evaluator.evaluate(
            snapshot=make_snapshot(make_path()),
            measurement=make_measurement(),
            policies=[policy()],  # type: ignore[arg-type]
        )


def test_traffic_stalled_grace_period_defaults_to_15_seconds() -> None:
    from datetime import timedelta

    value = policy()

    assert (
        value.traffic_stalled_grace_period
        == timedelta(seconds=15)
    )


def test_traffic_stalled_grace_period_can_be_configured() -> None:
    from datetime import timedelta

    value = CriticalPathPolicy(
        path="ejtv",
        traffic_stalled_grace_period=timedelta(seconds=30),
    )

    assert (
        value.traffic_stalled_grace_period
        == timedelta(seconds=30)
    )


def test_negative_traffic_stalled_grace_period_is_rejected() -> None:
    from datetime import timedelta

    with pytest.raises(ValueError):
        CriticalPathPolicy(
            path="ejtv",
            traffic_stalled_grace_period=timedelta(seconds=-1),
        )


def test_invalid_traffic_stalled_grace_period_type_is_rejected() -> None:
    with pytest.raises(TypeError):
        CriticalPathPolicy(
            path="ejtv",
            traffic_stalled_grace_period=15,  # type: ignore[arg-type]
        )
