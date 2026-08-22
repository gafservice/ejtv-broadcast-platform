from datetime import UTC, datetime, timedelta

import pytest

from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
)
from app.noc.services.expected_session_evaluator import (
    ExpectedSessionEvaluation,
    ExpectedSessionState,
)
from app.noc.services.expected_session_stabilizer import (
    ExpectedSessionStabilization,
    ExpectedSessionStabilizer,
)


BASE_TIME = datetime(
    2026,
    8,
    22,
    23,
    50,
    tzinfo=UTC,
)


def build_policy(
    *,
    policy_id: str = "ejtv-srt-reader",
    grace_seconds: int = 15,
) -> ExpectedSessionPolicy:
    return ExpectedSessionPolicy(
        policy_id=policy_id,
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="ejtv",
        missing_grace_period=timedelta(
            seconds=grace_seconds
        ),
    )


def build_evaluation(
    *,
    state: ExpectedSessionState,
    policy: ExpectedSessionPolicy | None = None,
) -> ExpectedSessionEvaluation:
    return ExpectedSessionEvaluation(
        policy=policy or build_policy(),
        state=state,
        matching_sessions=(),
    )


def test_first_missing_observation_starts_grace_period() -> None:
    stabilizer = ExpectedSessionStabilizer()

    result = stabilizer.stabilize(
        evaluation=build_evaluation(
            state=ExpectedSessionState.MISSING,
        ),
        observed_at=BASE_TIME,
    )

    assert isinstance(
        result,
        ExpectedSessionStabilization,
    )
    assert result.missing_since == BASE_TIME
    assert result.confirmed_missing is False


def test_missing_before_grace_period_is_not_confirmed() -> None:
    stabilizer = ExpectedSessionStabilizer()

    evaluation = build_evaluation(
        state=ExpectedSessionState.MISSING,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=14),
    )

    assert result.missing_since == BASE_TIME
    assert result.confirmed_missing is False


def test_missing_at_grace_period_is_confirmed() -> None:
    stabilizer = ExpectedSessionStabilizer()

    evaluation = build_evaluation(
        state=ExpectedSessionState.MISSING,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=15),
    )

    assert result.missing_since == BASE_TIME
    assert result.confirmed_missing is True


def test_missing_after_grace_period_remains_confirmed() -> None:
    stabilizer = ExpectedSessionStabilizer()

    evaluation = build_evaluation(
        state=ExpectedSessionState.MISSING,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=60),
    )

    assert result.confirmed_missing is True


def test_zero_grace_period_confirms_immediately() -> None:
    stabilizer = ExpectedSessionStabilizer()

    result = stabilizer.stabilize(
        evaluation=build_evaluation(
            state=ExpectedSessionState.MISSING,
            policy=build_policy(
                grace_seconds=0,
            ),
        ),
        observed_at=BASE_TIME,
    )

    assert result.confirmed_missing is True


def test_present_clears_missing_history() -> None:
    stabilizer = ExpectedSessionStabilizer()

    policy = build_policy()

    missing = build_evaluation(
        state=ExpectedSessionState.MISSING,
        policy=policy,
    )

    stabilizer.stabilize(
        evaluation=missing,
        observed_at=BASE_TIME,
    )

    present = ExpectedSessionEvaluation(
        policy=policy,
        state=ExpectedSessionState.PRESENT,
        matching_sessions=(
            build_dummy_session(),
        ),
    )

    result = stabilizer.stabilize(
        evaluation=present,
        observed_at=BASE_TIME + timedelta(seconds=5),
    )

    assert result.missing_since is None
    assert result.confirmed_missing is False


def test_new_missing_period_starts_after_recovery() -> None:
    stabilizer = ExpectedSessionStabilizer()

    policy = build_policy()

    missing = build_evaluation(
        state=ExpectedSessionState.MISSING,
        policy=policy,
    )

    stabilizer.stabilize(
        evaluation=missing,
        observed_at=BASE_TIME,
    )

    present = ExpectedSessionEvaluation(
        policy=policy,
        state=ExpectedSessionState.PRESENT,
        matching_sessions=(
            build_dummy_session(),
        ),
    )

    stabilizer.stabilize(
        evaluation=present,
        observed_at=BASE_TIME + timedelta(seconds=5),
    )

    second_missing_time = (
        BASE_TIME + timedelta(seconds=10)
    )

    result = stabilizer.stabilize(
        evaluation=missing,
        observed_at=second_missing_time,
    )

    assert result.missing_since == second_missing_time
    assert result.confirmed_missing is False


def test_policy_histories_are_independent() -> None:
    stabilizer = ExpectedSessionStabilizer()

    first = build_evaluation(
        state=ExpectedSessionState.MISSING,
        policy=build_policy(
            policy_id="first",
        ),
    )

    second = build_evaluation(
        state=ExpectedSessionState.MISSING,
        policy=build_policy(
            policy_id="second",
        ),
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

    assert first_result.confirmed_missing is True
    assert second_result.confirmed_missing is False


def test_observations_must_not_move_backwards() -> None:
    stabilizer = ExpectedSessionStabilizer()

    evaluation = build_evaluation(
        state=ExpectedSessionState.MISSING,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    with pytest.raises(
        ValueError,
        match=(
            "expected session observations must not "
            "move backwards in time"
        ),
    ):
        stabilizer.stabilize(
            evaluation=evaluation,
            observed_at=BASE_TIME - timedelta(seconds=1),
        )


def test_reset_one_policy() -> None:
    stabilizer = ExpectedSessionStabilizer()

    evaluation = build_evaluation(
        state=ExpectedSessionState.MISSING,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    stabilizer.reset("ejtv-srt-reader")

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=30),
    )

    assert (
        result.missing_since
        == BASE_TIME + timedelta(seconds=30)
    )
    assert result.confirmed_missing is False


def test_reset_all_policies() -> None:
    stabilizer = ExpectedSessionStabilizer()

    evaluation = build_evaluation(
        state=ExpectedSessionState.MISSING,
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

    assert result.confirmed_missing is False


def build_dummy_session():
    from app.domain.sessions import ActiveSession

    return ActiveSession(
        session_id="session-present",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="read",
        remote_ip="201.192.154.132",
        remote_port=50000,
        path="ejtv",
        connected_since=BASE_TIME,
    )
