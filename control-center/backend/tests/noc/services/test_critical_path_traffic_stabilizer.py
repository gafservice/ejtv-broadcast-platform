from datetime import datetime, timedelta, timezone

import pytest

from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingPathMeasurement,
)
from app.domain.streaming.models import (
    MediaPath,
    MediaPathStatus,
    MediaSource,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.services.critical_path_traffic_evaluator import (
    CriticalPathTrafficEvaluation,
    CriticalPathTrafficState,
)
from app.noc.services.critical_path_traffic_stabilizer import (
    CriticalPathTrafficStabilizer,
)


BASE = datetime(
    2026,
    8,
    31,
    8,
    0,
    tzinfo=timezone.utc,
)


def make_policy(
    grace_seconds: int = 15,
) -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path="ejtv",
        traffic_stalled_grace_period=timedelta(
            seconds=grace_seconds
        ),
    )


def make_media_path() -> MediaPath:
    return MediaPath(
        name="ejtv",
        configuration_name="ejtv",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="mpegtsSource"
        ),
    )


def make_measurement(
    bitrate: float,
) -> StreamingPathMeasurement:
    return StreamingPathMeasurement(
        name="ejtv",
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=0,
        reader_delta=0,
        inbound_delta_bytes=0,
        outbound_delta_bytes=0,
        inbound_bitrate_bps=bitrate,
        outbound_bitrate_bps=0.0,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )


def make_evaluation(
    state: CriticalPathTrafficState,
    *,
    grace_seconds: int = 15,
) -> CriticalPathTrafficEvaluation:
    if state is CriticalPathTrafficState.INACTIVE:
        return CriticalPathTrafficEvaluation(
            policy=make_policy(grace_seconds),
            state=state,
            media_path=None,
            measurement=None,
        )

    media_path = make_media_path()

    if state is CriticalPathTrafficState.UNKNOWN:
        return CriticalPathTrafficEvaluation(
            policy=make_policy(grace_seconds),
            state=state,
            media_path=media_path,
            measurement=None,
        )

    bitrate = (
        0.0
        if state is CriticalPathTrafficState.STALLED
        else 4_500_000.0
    )

    return CriticalPathTrafficEvaluation(
        policy=make_policy(grace_seconds),
        state=state,
        media_path=media_path,
        measurement=make_measurement(bitrate),
    )


def test_first_stalled_observation_starts_candidate() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    result = stabilizer.stabilize(
        evaluation=make_evaluation(
            CriticalPathTrafficState.STALLED
        ),
        observed_at=BASE,
    )

    assert result.stalled_since == BASE
    assert result.confirmed_stalled is False


def test_stalled_before_grace_is_not_confirmed() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    evaluation = make_evaluation(
        CriticalPathTrafficState.STALLED
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE + timedelta(seconds=14),
    )

    assert result.stalled_since == BASE
    assert result.confirmed_stalled is False


def test_stalled_at_exact_grace_is_confirmed() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    evaluation = make_evaluation(
        CriticalPathTrafficState.STALLED
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE + timedelta(seconds=15),
    )

    assert result.stalled_since == BASE
    assert result.confirmed_stalled is True


def test_stalled_after_grace_remains_confirmed() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    evaluation = make_evaluation(
        CriticalPathTrafficState.STALLED
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE + timedelta(seconds=30),
    )

    assert result.confirmed_stalled is True


@pytest.mark.parametrize(
    "recovery_state",
    (
        CriticalPathTrafficState.HEALTHY,
        CriticalPathTrafficState.UNKNOWN,
        CriticalPathTrafficState.INACTIVE,
    ),
)
def test_non_stalled_state_clears_candidate(
    recovery_state: CriticalPathTrafficState,
) -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    stabilizer.stabilize(
        evaluation=make_evaluation(
            CriticalPathTrafficState.STALLED
        ),
        observed_at=BASE,
    )

    result = stabilizer.stabilize(
        evaluation=make_evaluation(recovery_state),
        observed_at=BASE + timedelta(seconds=5),
    )

    assert result.stalled_since is None
    assert result.confirmed_stalled is False


def test_stalled_after_recovery_starts_new_candidate() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    stabilizer.stabilize(
        evaluation=make_evaluation(
            CriticalPathTrafficState.STALLED
        ),
        observed_at=BASE,
    )

    stabilizer.stabilize(
        evaluation=make_evaluation(
            CriticalPathTrafficState.HEALTHY
        ),
        observed_at=BASE + timedelta(seconds=5),
    )

    result = stabilizer.stabilize(
        evaluation=make_evaluation(
            CriticalPathTrafficState.STALLED
        ),
        observed_at=BASE + timedelta(seconds=10),
    )

    assert (
        result.stalled_since
        == BASE + timedelta(seconds=10)
    )
    assert result.confirmed_stalled is False


def test_zero_grace_confirms_immediately() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    result = stabilizer.stabilize(
        evaluation=make_evaluation(
            CriticalPathTrafficState.STALLED,
            grace_seconds=0,
        ),
        observed_at=BASE,
    )

    assert result.confirmed_stalled is True


def test_backward_time_is_rejected() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    evaluation = make_evaluation(
        CriticalPathTrafficState.STALLED
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE,
    )

    with pytest.raises(ValueError):
        stabilizer.stabilize(
            evaluation=evaluation,
            observed_at=BASE - timedelta(seconds=1),
        )


def test_naive_observed_at_is_rejected() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    with pytest.raises(ValueError):
        stabilizer.stabilize(
            evaluation=make_evaluation(
                CriticalPathTrafficState.STALLED
            ),
            observed_at=datetime(2026, 8, 31, 8, 0),
        )


def test_invalid_evaluation_type_is_rejected() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    with pytest.raises(TypeError):
        stabilizer.stabilize(
            evaluation=object(),  # type: ignore[arg-type]
            observed_at=BASE,
        )


def test_reset_one_path_forgets_candidate() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    evaluation = make_evaluation(
        CriticalPathTrafficState.STALLED
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE,
    )

    stabilizer.reset("ejtv")

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE + timedelta(seconds=20),
    )

    assert (
        result.stalled_since
        == BASE + timedelta(seconds=20)
    )
    assert result.confirmed_stalled is False


def test_reset_all_forgets_candidate() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    evaluation = make_evaluation(
        CriticalPathTrafficState.STALLED
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE,
    )

    stabilizer.reset()

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE + timedelta(seconds=20),
    )

    assert (
        result.stalled_since
        == BASE + timedelta(seconds=20)
    )


def test_invalid_reset_path_type_is_rejected() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    with pytest.raises(TypeError):
        stabilizer.reset(123)  # type: ignore[arg-type]


def test_empty_reset_path_is_rejected() -> None:
    stabilizer = CriticalPathTrafficStabilizer()

    with pytest.raises(ValueError):
        stabilizer.reset("   ")
