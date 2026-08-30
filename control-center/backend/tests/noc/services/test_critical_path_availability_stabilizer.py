"""Tests for critical-path availability temporal stabilization."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.streaming.models import (
    MediaPath,
    MediaPathStatus,
    MediaSource,
)
from app.noc.domain.critical_path_policy import CriticalPathPolicy
from app.noc.services.critical_path_availability_evaluator import (
    CriticalPathAvailabilityEvaluation,
    CriticalPathAvailabilityState,
)
from app.noc.services.critical_path_availability_stabilizer import (
    CriticalPathAvailabilityStabilization,
    CriticalPathAvailabilityStabilizer,
)


BASE_TIME = datetime(
    2026, 8, 30, 4, 15, tzinfo=UTC
)


def build_policy(
    *,
    path: str = "ejtv",
    grace_seconds: int = 15,
) -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path=path,
        unavailable_grace_period=timedelta(
            seconds=grace_seconds
        ),
    )


def build_available_path(
    *,
    name: str = "ejtv",
) -> MediaPath:
    return MediaPath(
        name=name,
        configuration_name=name,
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="mpegtsSource",
        ),
    )


def build_evaluation(
    *,
    state: CriticalPathAvailabilityState,
    policy: CriticalPathPolicy | None = None,
) -> CriticalPathAvailabilityEvaluation:
    policy = policy or build_policy()

    media_path = (
        build_available_path(name=policy.path)
        if state is CriticalPathAvailabilityState.AVAILABLE
        else None
    )

    return CriticalPathAvailabilityEvaluation(
        policy=policy,
        state=state,
        media_path=media_path,
    )


def test_first_unavailable_starts_grace_period() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()

    result = stabilizer.stabilize(
        evaluation=build_evaluation(
            state=CriticalPathAvailabilityState.UNAVAILABLE,
        ),
        observed_at=BASE_TIME,
    )

    assert isinstance(
        result,
        CriticalPathAvailabilityStabilization,
    )
    assert result.unavailable_since == BASE_TIME
    assert result.confirmed_unavailable is False


def test_before_grace_period_is_not_confirmed() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()
    evaluation = build_evaluation(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=14),
    )

    assert result.confirmed_unavailable is False


def test_at_grace_period_is_confirmed() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()
    evaluation = build_evaluation(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=15),
    )

    assert result.confirmed_unavailable is True
    assert result.unavailable_since == BASE_TIME


def test_zero_grace_period_confirms_immediately() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()

    result = stabilizer.stabilize(
        evaluation=build_evaluation(
            state=CriticalPathAvailabilityState.UNAVAILABLE,
            policy=build_policy(grace_seconds=0),
        ),
        observed_at=BASE_TIME,
    )

    assert result.confirmed_unavailable is True


def test_available_clears_candidate() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()

    unavailable = build_evaluation(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
    )

    stabilizer.stabilize(
        evaluation=unavailable,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        evaluation=build_evaluation(
            state=CriticalPathAvailabilityState.AVAILABLE,
        ),
        observed_at=BASE_TIME + timedelta(seconds=5),
    )

    assert result.unavailable_since is None
    assert result.confirmed_unavailable is False


def test_new_unavailable_period_starts_after_recovery() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()

    unavailable = build_evaluation(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
    )

    stabilizer.stabilize(
        evaluation=unavailable,
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        evaluation=build_evaluation(
            state=CriticalPathAvailabilityState.AVAILABLE,
        ),
        observed_at=BASE_TIME + timedelta(seconds=5),
    )

    second_start = BASE_TIME + timedelta(seconds=10)

    result = stabilizer.stabilize(
        evaluation=unavailable,
        observed_at=second_start,
    )

    assert result.unavailable_since == second_start
    assert result.confirmed_unavailable is False


def test_path_histories_are_independent() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()

    first = build_evaluation(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
        policy=build_policy(path="ejtv"),
    )
    second = build_evaluation(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
        policy=build_policy(path="enlace"),
    )

    stabilizer.stabilize(
        evaluation=first,
        observed_at=BASE_TIME,
    )
    stabilizer.stabilize(
        evaluation=second,
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    first_result = stabilizer.stabilize(
        evaluation=first,
        observed_at=BASE_TIME + timedelta(seconds=15),
    )
    second_result = stabilizer.stabilize(
        evaluation=second,
        observed_at=BASE_TIME + timedelta(seconds=15),
    )

    assert first_result.confirmed_unavailable is True
    assert second_result.confirmed_unavailable is False


def test_observations_must_not_move_backwards() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()
    evaluation = build_evaluation(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    with pytest.raises(
        ValueError,
        match=(
            "critical path observations must not "
            "move backwards in time"
        ),
    ):
        stabilizer.stabilize(
            evaluation=evaluation,
            observed_at=BASE_TIME - timedelta(seconds=1),
        )


def test_reset_one_path() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()
    evaluation = build_evaluation(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    stabilizer.reset("ejtv")

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=30),
    )

    assert (
        result.unavailable_since
        == BASE_TIME + timedelta(seconds=30)
    )
    assert result.confirmed_unavailable is False


def test_reset_all_paths() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()
    evaluation = build_evaluation(
        state=CriticalPathAvailabilityState.UNAVAILABLE,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    stabilizer.reset()

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=30),
    )

    assert result.confirmed_unavailable is False


def test_invalid_evaluation_is_rejected() -> None:
    stabilizer = CriticalPathAvailabilityStabilizer()

    with pytest.raises(
        TypeError,
        match=(
            "evaluation must be a "
            "CriticalPathAvailabilityEvaluation"
        ),
    ):
        stabilizer.stabilize(
            evaluation="invalid",  # type: ignore[arg-type]
            observed_at=BASE_TIME,
        )
