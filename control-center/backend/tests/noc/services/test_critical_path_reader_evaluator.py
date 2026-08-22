from datetime import UTC, datetime

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderEvaluation,
    CriticalPathReaderEvaluator,
    CriticalPathReaderState,
)


TIMESTAMP = datetime(
    2026,
    8,
    23,
    3,
    0,
    tzinfo=UTC,
)


def build_session(
    *,
    session_id: str,
    role: SessionRole,
    path: str = "ejtv",
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=role,
        state="read",
        remote_ip="201.192.154.132",
        remote_port=50000,
        path=path,
        connected_since=TIMESTAMP,
    )


def build_snapshot(
    *sessions: ActiveSession,
) -> SessionSnapshot:
    return SessionSnapshot(
        captured_at=TIMESTAMP,
        sessions=tuple(sessions),
    )


def build_policy(
    *,
    path: str = "ejtv",
    enabled: bool = True,
) -> CriticalPathPolicy:
    return CriticalPathPolicy(
        path=path,
        enabled=enabled,
    )


def test_state_string_representation() -> None:
    assert str(
        CriticalPathReaderState.INACTIVE
    ) == "INACTIVE"

    assert str(
        CriticalPathReaderState.HAS_READERS
    ) == "HAS_READERS"

    assert str(
        CriticalPathReaderState.NO_READERS
    ) == "NO_READERS"

    assert str(
        CriticalPathReaderState.INCONSISTENT
    ) == "INCONSISTENT"


def test_inactive_path_is_detected() -> None:
    evaluator = CriticalPathReaderEvaluator()

    result = evaluator.evaluate(
        snapshot=build_snapshot(),
        policies=(build_policy(),),
    )

    assert len(result) == 1
    assert (
        result[0].state
        is CriticalPathReaderState.INACTIVE
    )
    assert result[0].publishers == ()
    assert result[0].readers == ()


def test_publisher_with_reader_has_readers() -> None:
    evaluator = CriticalPathReaderEvaluator()

    publisher = build_session(
        session_id="publisher-1",
        role=SessionRole.PUBLISHER,
    )

    reader = build_session(
        session_id="reader-1",
        role=SessionRole.READER,
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(
            publisher,
            reader,
        ),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.HAS_READERS
    )

    assert result[0].publishers == (
        publisher,
    )

    assert result[0].readers == (
        reader,
    )


def test_publisher_without_readers_is_no_readers() -> None:
    evaluator = CriticalPathReaderEvaluator()

    publisher = build_session(
        session_id="publisher-1",
        role=SessionRole.PUBLISHER,
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(
            publisher,
        ),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.NO_READERS
    )

    assert result[0].publishers == (
        publisher,
    )

    assert result[0].readers == ()


def test_reader_without_publisher_is_inconsistent() -> None:
    evaluator = CriticalPathReaderEvaluator()

    reader = build_session(
        session_id="reader-1",
        role=SessionRole.READER,
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(
            reader,
        ),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.INCONSISTENT
    )

    assert result[0].publishers == ()
    assert result[0].readers == (
        reader,
    )


def test_sessions_on_other_paths_are_ignored() -> None:
    evaluator = CriticalPathReaderEvaluator()

    publisher = build_session(
        session_id="publisher-other",
        role=SessionRole.PUBLISHER,
        path="enlace",
    )

    reader = build_session(
        session_id="reader-other",
        role=SessionRole.READER,
        path="enlace",
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(
            publisher,
            reader,
        ),
        policies=(
            build_policy(
                path="ejtv",
            ),
        ),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.INACTIVE
    )


def test_multiple_readers_are_preserved() -> None:
    evaluator = CriticalPathReaderEvaluator()

    publisher = build_session(
        session_id="publisher-1",
        role=SessionRole.PUBLISHER,
    )

    first_reader = build_session(
        session_id="reader-1",
        role=SessionRole.READER,
    )

    second_reader = build_session(
        session_id="reader-2",
        role=SessionRole.READER,
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(
            publisher,
            first_reader,
            second_reader,
        ),
        policies=(build_policy(),),
    )

    assert (
        result[0].state
        is CriticalPathReaderState.HAS_READERS
    )

    assert result[0].readers == (
        first_reader,
        second_reader,
    )


def test_disabled_policy_is_not_evaluated() -> None:
    evaluator = CriticalPathReaderEvaluator()

    result = evaluator.evaluate(
        snapshot=build_snapshot(),
        policies=(
            build_policy(
                enabled=False,
            ),
        ),
    )

    assert result == ()


def test_multiple_policies_are_sorted_by_path() -> None:
    evaluator = CriticalPathReaderEvaluator()

    result = evaluator.evaluate(
        snapshot=build_snapshot(),
        policies=(
            build_policy(
                path="z-path",
            ),
            build_policy(
                path="a-path",
            ),
        ),
    )

    assert tuple(
        evaluation.policy.path
        for evaluation in result
    ) == (
        "a-path",
        "z-path",
    )


def test_duplicate_paths_are_rejected() -> None:
    evaluator = CriticalPathReaderEvaluator()

    with pytest.raises(
        ValueError,
        match=(
            "policies must not contain duplicate "
            "path values"
        ),
    ):
        evaluator.evaluate(
            snapshot=build_snapshot(),
            policies=(
                build_policy(
                    path="ejtv",
                ),
                build_policy(
                    path="ejtv",
                ),
            ),
        )


def test_invalid_snapshot_is_rejected() -> None:
    evaluator = CriticalPathReaderEvaluator()

    with pytest.raises(
        TypeError,
        match="snapshot must be a SessionSnapshot",
    ):
        evaluator.evaluate(
            snapshot="invalid",  # type: ignore[arg-type]
            policies=(),
        )


def test_non_tuple_policies_are_rejected() -> None:
    evaluator = CriticalPathReaderEvaluator()

    with pytest.raises(
        TypeError,
        match="policies must be a tuple",
    ):
        evaluator.evaluate(
            snapshot=build_snapshot(),
            policies=[],  # type: ignore[arg-type]
        )


def test_invalid_policy_member_is_rejected() -> None:
    evaluator = CriticalPathReaderEvaluator()

    with pytest.raises(
        TypeError,
        match=(
            "policies must contain only "
            "CriticalPathPolicy values"
        ),
    ):
        evaluator.evaluate(
            snapshot=build_snapshot(),
            policies=(
                "invalid",  # type: ignore[arg-type]
            ),
        )


def test_evaluation_rejects_invalid_policy() -> None:
    with pytest.raises(
        TypeError,
        match="policy must be a CriticalPathPolicy",
    ):
        CriticalPathReaderEvaluation(
            policy="invalid",  # type: ignore[arg-type]
            state=CriticalPathReaderState.INACTIVE,
            publishers=(),
            readers=(),
        )


def test_no_readers_requires_publisher() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "NO_READERS evaluation requires "
            "at least one publisher"
        ),
    ):
        CriticalPathReaderEvaluation(
            policy=build_policy(),
            state=CriticalPathReaderState.NO_READERS,
            publishers=(),
            readers=(),
        )


def test_inconsistent_requires_reader() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "INCONSISTENT evaluation requires "
            "at least one reader"
        ),
    ):
        CriticalPathReaderEvaluation(
            policy=build_policy(),
            state=CriticalPathReaderState.INCONSISTENT,
            publishers=(),
            readers=(),
        )
