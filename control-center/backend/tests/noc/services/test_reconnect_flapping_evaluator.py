from datetime import UTC, datetime, timedelta

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.logical_session_identity import (
    LogicalSessionIdentity,
)
from app.noc.domain.reconnect_flapping_policy import (
    ReconnectFlappingPolicy,
)
from app.noc.services.reconnect_flapping_evaluator import (
    ReconnectFlappingEvaluation,
    ReconnectFlappingEvaluator,
    ReconnectFlappingState,
)
from app.noc.services.session_transition_detector import (
    SessionTransition,
    SessionTransitionKind,
)


BASE_TIME = datetime(
    2026,
    8,
    23,
    1,
    30,
    tzinfo=UTC,
)


def build_session(
    *,
    session_id: str,
    remote_ip: str = "201.192.154.132",
    remote_port: int = 50000,
    path: str = "ejtv",
    protocol: SessionProtocol = SessionProtocol.SRT,
    role: SessionRole = SessionRole.READER,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
        role=role,
        state="read",
        remote_ip=remote_ip,
        remote_port=remote_port,
        path=path,
        connected_since=BASE_TIME,
    )


def transition(
    *,
    kind: SessionTransitionKind,
    session_id: str,
    remote_ip: str = "201.192.154.132",
    remote_port: int = 50000,
    path: str = "ejtv",
) -> SessionTransition:
    return SessionTransition(
        session=build_session(
            session_id=session_id,
            remote_ip=remote_ip,
            remote_port=remote_port,
            path=path,
        ),
        kind=kind,
    )


def test_state_string_representation() -> None:
    assert str(
        ReconnectFlappingState.STABLE
    ) == "STABLE"

    assert str(
        ReconnectFlappingState.FLAPPING
    ) == "FLAPPING"


def test_default_policy_is_created() -> None:
    evaluator = ReconnectFlappingEvaluator()

    assert isinstance(
        evaluator.policy,
        ReconnectFlappingPolicy,
    )


def test_disconnect_alone_is_not_reconnect() -> None:
    evaluator = ReconnectFlappingEvaluator()

    result = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
        ),
        observed_at=BASE_TIME,
    )

    assert isinstance(
        result,
        ReconnectFlappingEvaluation,
    )
    assert result.reconnect_detected is False
    assert result.reconnect_count == 0
    assert result.state is ReconnectFlappingState.STABLE


def test_disconnect_then_connect_is_reconnect() -> None:
    evaluator = ReconnectFlappingEvaluator()

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
        ),
        observed_at=BASE_TIME,
    )

    result = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-session",
            remote_port=51783,
        ),
        observed_at=BASE_TIME + timedelta(seconds=2),
    )

    assert result.reconnect_detected is True
    assert result.reconnect_count == 1
    assert result.state is ReconnectFlappingState.STABLE


def test_connect_after_timeout_is_not_reconnect() -> None:
    evaluator = ReconnectFlappingEvaluator()

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
        ),
        observed_at=BASE_TIME,
    )

    result = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-session",
        ),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert result.reconnect_detected is False
    assert result.reconnect_count == 0
    assert result.state is ReconnectFlappingState.STABLE


def test_three_reconnects_inside_window_trigger_flapping() -> None:
    evaluator = ReconnectFlappingEvaluator()

    timestamps = (
        (0, 2),
        (10, 12),
        (20, 22),
    )

    result = None

    for index, (
        disconnect_second,
        connect_second,
    ) in enumerate(timestamps):
        evaluator.evaluate(
            transition=transition(
                kind=SessionTransitionKind.DISCONNECTED,
                session_id=f"old-{index}",
            ),
            observed_at=(
                BASE_TIME
                + timedelta(
                    seconds=disconnect_second
                )
            ),
        )

        result = evaluator.evaluate(
            transition=transition(
                kind=SessionTransitionKind.CONNECTED,
                session_id=f"new-{index}",
                remote_port=50000 + index,
            ),
            observed_at=(
                BASE_TIME
                + timedelta(
                    seconds=connect_second
                )
            ),
        )

    assert result is not None
    assert result.reconnect_count == 3
    assert result.reconnect_detected is True
    assert result.state is ReconnectFlappingState.FLAPPING


def test_reconnects_outside_window_do_not_trigger_flapping() -> None:
    evaluator = ReconnectFlappingEvaluator(
        policy=ReconnectFlappingPolicy(
            reconnect_timeout=timedelta(seconds=10),
            window=timedelta(seconds=30),
            threshold=3,
        )
    )

    reconnect_times = (
        (0, 1),
        (20, 21),
        (40, 41),
    )

    result = None

    for index, (
        disconnect_second,
        connect_second,
    ) in enumerate(reconnect_times):
        evaluator.evaluate(
            transition=transition(
                kind=SessionTransitionKind.DISCONNECTED,
                session_id=f"old-{index}",
            ),
            observed_at=(
                BASE_TIME
                + timedelta(
                    seconds=disconnect_second
                )
            ),
        )

        result = evaluator.evaluate(
            transition=transition(
                kind=SessionTransitionKind.CONNECTED,
                session_id=f"new-{index}",
            ),
            observed_at=(
                BASE_TIME
                + timedelta(
                    seconds=connect_second
                )
            ),
        )

    assert result is not None
    assert result.reconnect_count == 2
    assert result.state is ReconnectFlappingState.STABLE


def test_remote_port_change_preserves_identity() -> None:
    evaluator = ReconnectFlappingEvaluator()

    first = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
            remote_port=50000,
        ),
        observed_at=BASE_TIME,
    )

    second = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-session",
            remote_port=60000,
        ),
        observed_at=BASE_TIME + timedelta(seconds=2),
    )

    assert first.identity == second.identity
    assert second.reconnect_detected is True


def test_different_remote_ip_does_not_pair_reconnect() -> None:
    evaluator = ReconnectFlappingEvaluator()

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
            remote_ip="201.192.154.132",
        ),
        observed_at=BASE_TIME,
    )

    result = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-session",
            remote_ip="190.10.20.30",
        ),
        observed_at=BASE_TIME + timedelta(seconds=2),
    )

    assert result.reconnect_detected is False
    assert result.reconnect_count == 0


def test_histories_are_independent_by_identity() -> None:
    evaluator = ReconnectFlappingEvaluator(
        policy=ReconnectFlappingPolicy(
            threshold=2,
        )
    )

    first_ip = "201.192.154.132"
    second_ip = "190.10.20.30"

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="a-old-1",
            remote_ip=first_ip,
        ),
        observed_at=BASE_TIME,
    )

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="a-new-1",
            remote_ip=first_ip,
        ),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="a-old-2",
            remote_ip=first_ip,
        ),
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    first_result = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="a-new-2",
            remote_ip=first_ip,
        ),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    second_result = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="b-new",
            remote_ip=second_ip,
        ),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert (
        first_result.state
        is ReconnectFlappingState.FLAPPING
    )

    assert (
        second_result.state
        is ReconnectFlappingState.STABLE
    )


def test_pending_disconnect_is_consumed_once() -> None:
    evaluator = ReconnectFlappingEvaluator()

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
        ),
        observed_at=BASE_TIME,
    )

    first_connect = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-session",
        ),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    second_connect = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="another-session",
        ),
        observed_at=BASE_TIME + timedelta(seconds=2),
    )

    assert first_connect.reconnect_detected is True
    assert second_connect.reconnect_detected is False
    assert second_connect.reconnect_count == 1


def test_observations_must_not_move_backwards() -> None:
    evaluator = ReconnectFlappingEvaluator()

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
        ),
        observed_at=BASE_TIME,
    )

    with pytest.raises(
        ValueError,
        match=(
            "reconnect observations must not "
            "move backwards in time"
        ),
    ):
        evaluator.evaluate(
            transition=transition(
                kind=SessionTransitionKind.CONNECTED,
                session_id="new-session",
            ),
            observed_at=BASE_TIME - timedelta(seconds=1),
        )


def test_reset_identity_clears_history() -> None:
    evaluator = ReconnectFlappingEvaluator()

    disconnected = transition(
        kind=SessionTransitionKind.DISCONNECTED,
        session_id="old-session",
    )

    evaluator.evaluate(
        transition=disconnected,
        observed_at=BASE_TIME,
    )

    identity = LogicalSessionIdentity.from_session(
        disconnected.session
    )

    evaluator.reset(identity)

    result = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-session",
        ),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result.reconnect_detected is False
    assert result.reconnect_count == 0


def test_invalid_transition_is_rejected() -> None:
    evaluator = ReconnectFlappingEvaluator()

    with pytest.raises(
        TypeError,
        match="transition must be a SessionTransition",
    ):
        evaluator.evaluate(
            transition="invalid",  # type: ignore[arg-type]
            observed_at=BASE_TIME,
        )


def test_naive_observed_at_is_rejected() -> None:
    evaluator = ReconnectFlappingEvaluator()

    with pytest.raises(
        ValueError,
        match="observed_at must be timezone-aware",
    ):
        evaluator.evaluate(
            transition=transition(
                kind=SessionTransitionKind.DISCONNECTED,
                session_id="old-session",
            ),
            observed_at=datetime(
                2026,
                8,
                23,
                1,
                30,
            ),
        )


def test_observe_ages_flapping_back_to_stable() -> None:
    evaluator = ReconnectFlappingEvaluator(
        policy=ReconnectFlappingPolicy(
            reconnect_timeout=timedelta(seconds=10),
            window=timedelta(seconds=30),
            threshold=2,
        )
    )

    # Reconnect #1 at t=1.
    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-1",
        ),
        observed_at=BASE_TIME,
    )

    first = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-1",
        ),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    # Reconnect #2 at t=11 -> FLAPPING.
    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-2",
        ),
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    flapping = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-2",
        ),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert first.state is ReconnectFlappingState.STABLE
    assert flapping.state is ReconnectFlappingState.FLAPPING

    # Same logical relationship, no additional transitions.
    stable = evaluator.observe(
        identity=flapping.identity,
        observed_at=BASE_TIME + timedelta(seconds=42),
    )

    assert stable.reconnect_detected is False
    assert stable.reconnect_count == 0
    assert stable.reconnect_timestamps == ()
    assert stable.state is ReconnectFlappingState.STABLE


def test_observe_preserves_flapping_while_threshold_remains() -> None:
    evaluator = ReconnectFlappingEvaluator(
        policy=ReconnectFlappingPolicy(
            reconnect_timeout=timedelta(seconds=10),
            window=timedelta(seconds=60),
            threshold=2,
        )
    )

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-1",
        ),
        observed_at=BASE_TIME,
    )

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-1",
        ),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-2",
        ),
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    flapping = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-2",
        ),
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    observed = evaluator.observe(
        identity=flapping.identity,
        observed_at=BASE_TIME + timedelta(seconds=30),
    )

    assert observed.state is ReconnectFlappingState.FLAPPING
    assert observed.reconnect_count == 2
    assert observed.reconnect_detected is False


def test_observe_unknown_identity_returns_stable() -> None:
    evaluator = ReconnectFlappingEvaluator()

    identity = LogicalSessionIdentity(
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="ejtv",
        remote_ip="201.192.154.132",
    )

    result = evaluator.observe(
        identity=identity,
        observed_at=BASE_TIME,
    )

    assert result.identity == identity
    assert result.state is ReconnectFlappingState.STABLE
    assert result.reconnect_count == 0
    assert result.reconnect_detected is False


def test_observe_rejects_invalid_identity() -> None:
    evaluator = ReconnectFlappingEvaluator()

    with pytest.raises(
        TypeError,
        match="identity must be a LogicalSessionIdentity",
    ):
        evaluator.observe(
            identity="invalid",  # type: ignore[arg-type]
            observed_at=BASE_TIME,
        )


def test_observe_must_not_move_backwards() -> None:
    evaluator = ReconnectFlappingEvaluator()

    disconnected = transition(
        kind=SessionTransitionKind.DISCONNECTED,
        session_id="old-session",
    )

    result = evaluator.evaluate(
        transition=disconnected,
        observed_at=BASE_TIME,
    )

    with pytest.raises(
        ValueError,
        match=(
            "reconnect observations must not "
            "move backwards in time"
        ),
    ):
        evaluator.observe(
            identity=result.identity,
            observed_at=BASE_TIME - timedelta(seconds=1),
        )


def test_identities_empty_initially() -> None:
    evaluator = ReconnectFlappingEvaluator()

    assert evaluator.identities() == ()


def test_identities_contains_observed_identity() -> None:
    evaluator = ReconnectFlappingEvaluator()

    result = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
        ),
        observed_at=BASE_TIME,
    )

    assert evaluator.identities() == (
        result.identity,
    )


def test_identities_are_unique_across_reconnections() -> None:
    evaluator = ReconnectFlappingEvaluator()

    first = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
            remote_port=50000,
        ),
        observed_at=BASE_TIME,
    )

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.CONNECTED,
            session_id="new-session",
            remote_port=60000,
        ),
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert evaluator.identities() == (
        first.identity,
    )


def test_identities_are_deterministically_sorted() -> None:
    evaluator = ReconnectFlappingEvaluator()

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="second",
            remote_ip="201.192.154.132",
            path="z-path",
        ),
        observed_at=BASE_TIME,
    )

    evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="first",
            remote_ip="190.10.20.30",
            path="a-path",
        ),
        observed_at=BASE_TIME,
    )

    identities = evaluator.identities()

    assert tuple(
        identity.path
        for identity in identities
    ) == (
        "a-path",
        "z-path",
    )


def test_reset_removes_identity_from_identities() -> None:
    evaluator = ReconnectFlappingEvaluator()

    result = evaluator.evaluate(
        transition=transition(
            kind=SessionTransitionKind.DISCONNECTED,
            session_id="old-session",
        ),
        observed_at=BASE_TIME,
    )

    evaluator.reset(result.identity)

    assert evaluator.identities() == ()
