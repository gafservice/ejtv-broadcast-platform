from datetime import UTC, datetime, timedelta

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderEvaluation,
    CriticalPathReaderState,
)
from app.noc.services.critical_path_reader_stabilizer import (
    CriticalPathReaderStabilization,
    CriticalPathReaderStabilizer,
)


BASE_TIME = datetime(
    2026,
    8,
    23,
    3,
    15,
    tzinfo=UTC,
)


def build_policy(
    *,
    path: str = "ejtv",
    grace_seconds: int = 15,
) -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path=path,
        no_readers_grace_period=timedelta(
            seconds=grace_seconds
        ),
    )


def build_session(
    *,
    session_id: str,
    role: SessionRole,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=role,
        state="read",
        remote_ip="201.192.154.132",
        remote_port=50000,
        path="ejtv",
        connected_since=BASE_TIME,
    )


def build_evaluation(
    *,
    state: CriticalPathReaderState,
    policy: CriticalPathPolicy | None = None,
) -> CriticalPathReaderEvaluation:
    policy = policy or build_policy()

    if state is CriticalPathReaderState.NO_READERS:
        publishers = (
            build_session(
                session_id="publisher-1",
                role=SessionRole.PUBLISHER,
            ),
        )
        readers = ()
    elif state is CriticalPathReaderState.HAS_READERS:
        publishers = (
            build_session(
                session_id="publisher-1",
                role=SessionRole.PUBLISHER,
            ),
        )
        readers = (
            build_session(
                session_id="reader-1",
                role=SessionRole.READER,
            ),
        )
    elif state is CriticalPathReaderState.INCONSISTENT:
        publishers = ()
        readers = (
            build_session(
                session_id="reader-1",
                role=SessionRole.READER,
            ),
        )
    else:
        publishers = ()
        readers = ()

    return CriticalPathReaderEvaluation(
        policy=policy,
        state=state,
        publishers=publishers,
        readers=readers,
    )


def test_first_no_readers_starts_grace_period() -> None:
    stabilizer = CriticalPathReaderStabilizer()

    result = stabilizer.stabilize(
        evaluation=build_evaluation(
            state=CriticalPathReaderState.NO_READERS,
        ),
        observed_at=BASE_TIME,
    )

    assert isinstance(
        result,
        CriticalPathReaderStabilization,
    )

    assert result.no_readers_since == BASE_TIME
    assert result.confirmed_no_readers is False


def test_before_grace_period_is_not_confirmed() -> None:
    stabilizer = CriticalPathReaderStabilizer()

    evaluation = build_evaluation(
        state=CriticalPathReaderState.NO_READERS,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=14),
    )

    assert result.confirmed_no_readers is False


def test_at_grace_period_is_confirmed() -> None:
    stabilizer = CriticalPathReaderStabilizer()

    evaluation = build_evaluation(
        state=CriticalPathReaderState.NO_READERS,
    )

    stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        evaluation=evaluation,
        observed_at=BASE_TIME + timedelta(seconds=15),
    )

    assert result.confirmed_no_readers is True
    assert result.no_readers_since == BASE_TIME


def test_zero_grace_period_confirms_immediately() -> None:
    stabilizer = CriticalPathReaderStabilizer()

    result = stabilizer.stabilize(
        evaluation=build_evaluation(
            state=CriticalPathReaderState.NO_READERS,
            policy=build_policy(
                grace_seconds=0,
            ),
        ),
        observed_at=BASE_TIME,
    )

    assert result.confirmed_no_readers is True


@pytest.mark.parametrize(
    "state",
    (
        CriticalPathReaderState.HAS_READERS,
        CriticalPathReaderState.INACTIVE,
        CriticalPathReaderState.INCONSISTENT,
    ),
)
def test_non_no_readers_clears_candidate(
    state: CriticalPathReaderState,
) -> None:
    stabilizer = CriticalPathReaderStabilizer()

    missing = build_evaluation(
        state=CriticalPathReaderState.NO_READERS,
    )

    stabilizer.stabilize(
        evaluation=missing,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        evaluation=build_evaluation(
            state=state,
        ),
        observed_at=BASE_TIME + timedelta(seconds=5),
    )

    assert result.no_readers_since is None
    assert result.confirmed_no_readers is False


def test_new_no_readers_period_starts_after_recovery() -> None:
    stabilizer = CriticalPathReaderStabilizer()

    no_readers = build_evaluation(
        state=CriticalPathReaderState.NO_READERS,
    )

    stabilizer.stabilize(
        evaluation=no_readers,
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        evaluation=build_evaluation(
            state=CriticalPathReaderState.HAS_READERS,
        ),
        observed_at=BASE_TIME + timedelta(seconds=5),
    )

    second_start = (
        BASE_TIME + timedelta(seconds=10)
    )

    result = stabilizer.stabilize(
        evaluation=no_readers,
        observed_at=second_start,
    )

    assert result.no_readers_since == second_start
    assert result.confirmed_no_readers is False


def test_path_histories_are_independent() -> None:
    stabilizer = CriticalPathReaderStabilizer()

    first_policy = build_policy(
        path="ejtv",
    )

    second_policy = build_policy(
        path="enlace",
    )

    first = build_evaluation(
        state=CriticalPathReaderState.NO_READERS,
        policy=first_policy,
    )

    second = build_evaluation(
        state=CriticalPathReaderState.NO_READERS,
        policy=second_policy,
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

    assert first_result.confirmed_no_readers is True
    assert second_result.confirmed_no_readers is False


def test_observations_must_not_move_backwards() -> None:
    stabilizer = CriticalPathReaderStabilizer()

    evaluation = build_evaluation(
        state=CriticalPathReaderState.NO_READERS,
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
    stabilizer = CriticalPathReaderStabilizer()

    evaluation = build_evaluation(
        state=CriticalPathReaderState.NO_READERS,
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
        result.no_readers_since
        == BASE_TIME + timedelta(seconds=30)
    )
    assert result.confirmed_no_readers is False


def test_reset_all_paths() -> None:
    stabilizer = CriticalPathReaderStabilizer()

    evaluation = build_evaluation(
        state=CriticalPathReaderState.NO_READERS,
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

    assert result.confirmed_no_readers is False


def test_invalid_evaluation_is_rejected() -> None:
    stabilizer = CriticalPathReaderStabilizer()

    with pytest.raises(
        TypeError,
        match=(
            "evaluation must be a "
            "CriticalPathReaderEvaluation"
        ),
    ):
        stabilizer.stabilize(
            evaluation="invalid",  # type: ignore[arg-type]
            observed_at=BASE_TIME,
        )
