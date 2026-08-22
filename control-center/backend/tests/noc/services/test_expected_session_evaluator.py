from datetime import UTC, datetime

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
)
from app.noc.services.expected_session_evaluator import (
    ExpectedSessionEvaluation,
    ExpectedSessionEvaluator,
    ExpectedSessionState,
)


TIMESTAMP = datetime(
    2026,
    8,
    22,
    23,
    45,
    tzinfo=UTC,
)


def build_session(
    *,
    session_id: str = "session-001",
    protocol: SessionProtocol = SessionProtocol.SRT,
    role: SessionRole = SessionRole.READER,
    path: str | None = "ejtv",
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
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
    policy_id: str = "ejtv-srt-reader",
    protocol: SessionProtocol = SessionProtocol.SRT,
    role: SessionRole = SessionRole.READER,
    path: str | None = "ejtv",
    enabled: bool = True,
) -> ExpectedSessionPolicy:
    return ExpectedSessionPolicy(
        policy_id=policy_id,
        protocol=protocol,
        role=role,
        path=path,
        enabled=enabled,
    )


def test_state_string_representation() -> None:
    assert str(
        ExpectedSessionState.PRESENT
    ) == "PRESENT"

    assert str(
        ExpectedSessionState.MISSING
    ) == "MISSING"


def test_present_policy_is_detected() -> None:
    evaluator = ExpectedSessionEvaluator()

    session = build_session()

    result = evaluator.evaluate(
        snapshot=build_snapshot(session),
        policies=(
            build_policy(),
        ),
    )

    assert len(result) == 1

    evaluation = result[0]

    assert (
        evaluation.state
        is ExpectedSessionState.PRESENT
    )

    assert evaluation.matching_sessions == (
        session,
    )


def test_missing_policy_is_detected() -> None:
    evaluator = ExpectedSessionEvaluator()

    result = evaluator.evaluate(
        snapshot=build_snapshot(),
        policies=(
            build_policy(),
        ),
    )

    assert len(result) == 1

    evaluation = result[0]

    assert (
        evaluation.state
        is ExpectedSessionState.MISSING
    )

    assert evaluation.matching_sessions == ()


def test_wrong_protocol_is_missing() -> None:
    evaluator = ExpectedSessionEvaluator()

    snapshot = build_snapshot(
        build_session(
            protocol=SessionProtocol.RTSP,
        )
    )

    result = evaluator.evaluate(
        snapshot=snapshot,
        policies=(
            build_policy(
                protocol=SessionProtocol.SRT,
            ),
        ),
    )

    assert (
        result[0].state
        is ExpectedSessionState.MISSING
    )


def test_wrong_role_is_missing() -> None:
    evaluator = ExpectedSessionEvaluator()

    snapshot = build_snapshot(
        build_session(
            role=SessionRole.PUBLISHER,
        )
    )

    result = evaluator.evaluate(
        snapshot=snapshot,
        policies=(
            build_policy(
                role=SessionRole.READER,
            ),
        ),
    )

    assert (
        result[0].state
        is ExpectedSessionState.MISSING
    )


def test_wrong_path_is_missing() -> None:
    evaluator = ExpectedSessionEvaluator()

    snapshot = build_snapshot(
        build_session(
            path="enlace",
        )
    )

    result = evaluator.evaluate(
        snapshot=snapshot,
        policies=(
            build_policy(
                path="ejtv",
            ),
        ),
    )

    assert (
        result[0].state
        is ExpectedSessionState.MISSING
    )


def test_multiple_matching_sessions_are_preserved() -> None:
    evaluator = ExpectedSessionEvaluator()

    first = build_session(
        session_id="session-a",
    )

    second = build_session(
        session_id="session-b",
    )

    result = evaluator.evaluate(
        snapshot=build_snapshot(
            first,
            second,
        ),
        policies=(
            build_policy(),
        ),
    )

    assert (
        result[0].state
        is ExpectedSessionState.PRESENT
    )

    assert result[0].matching_sessions == (
        first,
        second,
    )


def test_disabled_policy_is_not_evaluated() -> None:
    evaluator = ExpectedSessionEvaluator()

    result = evaluator.evaluate(
        snapshot=build_snapshot(),
        policies=(
            build_policy(
                enabled=False,
            ),
        ),
    )

    assert result == ()


def test_multiple_policies_are_sorted_by_policy_id() -> None:
    evaluator = ExpectedSessionEvaluator()

    result = evaluator.evaluate(
        snapshot=build_snapshot(),
        policies=(
            build_policy(
                policy_id="z-policy",
                path="z",
            ),
            build_policy(
                policy_id="a-policy",
                path="a",
            ),
        ),
    )

    assert tuple(
        evaluation.policy.policy_id
        for evaluation in result
    ) == (
        "a-policy",
        "z-policy",
    )


def test_duplicate_policy_ids_are_rejected() -> None:
    evaluator = ExpectedSessionEvaluator()

    with pytest.raises(
        ValueError,
        match=(
            "policies must not contain duplicate "
            "policy_id values"
        ),
    ):
        evaluator.evaluate(
            snapshot=build_snapshot(),
            policies=(
                build_policy(
                    policy_id="duplicate",
                    path="ejtv",
                ),
                build_policy(
                    policy_id="duplicate",
                    path="enlace",
                ),
            ),
        )


def test_evaluate_rejects_invalid_snapshot() -> None:
    evaluator = ExpectedSessionEvaluator()

    with pytest.raises(
        TypeError,
        match="snapshot must be a SessionSnapshot",
    ):
        evaluator.evaluate(
            snapshot="invalid",  # type: ignore[arg-type]
            policies=(),
        )


def test_evaluate_rejects_non_tuple_policies() -> None:
    evaluator = ExpectedSessionEvaluator()

    with pytest.raises(
        TypeError,
        match="policies must be a tuple",
    ):
        evaluator.evaluate(
            snapshot=build_snapshot(),
            policies=[],  # type: ignore[arg-type]
        )


def test_evaluate_rejects_invalid_policy_member() -> None:
    evaluator = ExpectedSessionEvaluator()

    with pytest.raises(
        TypeError,
        match=(
            "policies must contain only "
            "ExpectedSessionPolicy values"
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
        match="policy must be an ExpectedSessionPolicy",
    ):
        ExpectedSessionEvaluation(
            policy="invalid",  # type: ignore[arg-type]
            state=ExpectedSessionState.MISSING,
            matching_sessions=(),
        )


def test_evaluation_rejects_invalid_state() -> None:
    with pytest.raises(
        TypeError,
        match="state must be an ExpectedSessionState",
    ):
        ExpectedSessionEvaluation(
            policy=build_policy(),
            state="MISSING",  # type: ignore[arg-type]
            matching_sessions=(),
        )


def test_present_requires_matching_session() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "PRESENT evaluation requires at least "
            "one matching session"
        ),
    ):
        ExpectedSessionEvaluation(
            policy=build_policy(),
            state=ExpectedSessionState.PRESENT,
            matching_sessions=(),
        )


def test_missing_rejects_matching_sessions() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "MISSING evaluation must not contain "
            "matching sessions"
        ),
    ):
        ExpectedSessionEvaluation(
            policy=build_policy(),
            state=ExpectedSessionState.MISSING,
            matching_sessions=(
                build_session(),
            ),
        )
