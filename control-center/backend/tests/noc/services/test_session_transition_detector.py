from datetime import UTC, datetime

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.noc.services.session_transition_detector import (
    SessionTransition,
    SessionTransitionDetector,
    SessionTransitionKind,
)


NOW = datetime(
    2026,
    8,
    22,
    22,
    0,
    tzinfo=UTC,
)


def build_session(
    *,
    session_id: str,
    remote_ip: str = "201.192.154.132",
    remote_port: int = 50000,
    path: str = "ejtv",
    protocol: SessionProtocol = SessionProtocol.SRT,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
        role=SessionRole.READER,
        state="read",
        remote_ip=remote_ip,
        remote_port=remote_port,
        path=path,
        connected_since=NOW,
    )


def build_snapshot(
    *sessions: ActiveSession,
) -> SessionSnapshot:
    return SessionSnapshot(
        captured_at=NOW,
        sessions=tuple(sessions),
    )


def test_transition_kind_string_representation() -> None:
    assert (
        str(SessionTransitionKind.CONNECTED)
        == "CONNECTED"
    )

    assert (
        str(SessionTransitionKind.DISCONNECTED)
        == "DISCONNECTED"
    )


def test_transition_requires_active_session() -> None:
    with pytest.raises(
        TypeError,
        match="session must be an ActiveSession",
    ):
        SessionTransition(
            session="invalid",  # type: ignore[arg-type]
            kind=SessionTransitionKind.CONNECTED,
        )


def test_transition_requires_valid_kind() -> None:
    session = build_session(
        session_id="session-001",
    )

    with pytest.raises(
        TypeError,
        match="kind must be a SessionTransitionKind",
    ):
        SessionTransition(
            session=session,
            kind="CONNECTED",  # type: ignore[arg-type]
        )


def test_detect_requires_valid_previous() -> None:
    detector = SessionTransitionDetector()

    current = build_snapshot()

    with pytest.raises(
        TypeError,
        match="previous must be a SessionSnapshot or None",
    ):
        detector.detect(
            "invalid",  # type: ignore[arg-type]
            current,
        )


def test_detect_requires_valid_current() -> None:
    detector = SessionTransitionDetector()

    with pytest.raises(
        TypeError,
        match="current must be a SessionSnapshot",
    ):
        detector.detect(
            None,
            "invalid",  # type: ignore[arg-type]
        )


def test_first_snapshot_establishes_baseline() -> None:
    detector = SessionTransitionDetector()

    current = build_snapshot(
        build_session(
            session_id="session-001",
        ),
        build_session(
            session_id="session-002",
        ),
        build_session(
            session_id="session-003",
        ),
    )

    transitions = detector.detect(
        None,
        current,
    )

    assert transitions == ()


def test_identical_snapshots_produce_no_transition() -> None:
    detector = SessionTransitionDetector()

    session_a = build_session(
        session_id="session-a",
    )
    session_b = build_session(
        session_id="session-b",
    )

    previous = build_snapshot(
        session_a,
        session_b,
    )

    current = build_snapshot(
        session_a,
        session_b,
    )

    transitions = detector.detect(
        previous,
        current,
    )

    assert transitions == ()


def test_detects_connected_session() -> None:
    detector = SessionTransitionDetector()

    session_a = build_session(
        session_id="session-a",
    )
    session_b = build_session(
        session_id="session-b",
    )
    session_c = build_session(
        session_id="session-c",
    )

    previous = build_snapshot(
        session_a,
        session_b,
    )

    current = build_snapshot(
        session_a,
        session_b,
        session_c,
    )

    transitions = detector.detect(
        previous,
        current,
    )

    assert len(transitions) == 1

    transition = transitions[0]

    assert (
        transition.kind
        is SessionTransitionKind.CONNECTED
    )
    assert transition.session is session_c


def test_detects_disconnected_session() -> None:
    detector = SessionTransitionDetector()

    session_a = build_session(
        session_id="session-a",
    )
    session_b = build_session(
        session_id="session-b",
    )
    session_c = build_session(
        session_id="session-c",
    )

    previous = build_snapshot(
        session_a,
        session_b,
        session_c,
    )

    current = build_snapshot(
        session_a,
        session_c,
    )

    transitions = detector.detect(
        previous,
        current,
    )

    assert len(transitions) == 1

    transition = transitions[0]

    assert (
        transition.kind
        is SessionTransitionKind.DISCONNECTED
    )
    assert transition.session is session_b


def test_session_identity_is_session_id_not_remote_address() -> None:
    detector = SessionTransitionDetector()

    previous_session = build_session(
        session_id="old-session",
        remote_ip="201.192.154.132",
        remote_port=50000,
        path="ejtv",
        protocol=SessionProtocol.SRT,
    )

    current_session = build_session(
        session_id="new-session",
        remote_ip="201.192.154.132",
        remote_port=50000,
        path="ejtv",
        protocol=SessionProtocol.SRT,
    )

    previous = build_snapshot(
        previous_session,
    )

    current = build_snapshot(
        current_session,
    )

    transitions = detector.detect(
        previous,
        current,
    )

    assert len(transitions) == 2

    assert (
        transitions[0].kind
        is SessionTransitionKind.DISCONNECTED
    )
    assert (
        transitions[0].session.session_id
        == "old-session"
    )

    assert (
        transitions[1].kind
        is SessionTransitionKind.CONNECTED
    )
    assert (
        transitions[1].session.session_id
        == "new-session"
    )


def test_multiple_transitions_are_deterministic() -> None:
    detector = SessionTransitionDetector()

    previous = build_snapshot(
        build_session(
            session_id="session-b",
        ),
        build_session(
            session_id="session-d",
        ),
    )

    current = build_snapshot(
        build_session(
            session_id="session-a",
        ),
        build_session(
            session_id="session-c",
        ),
    )

    transitions = detector.detect(
        previous,
        current,
    )

    result = tuple(
        (
            transition.kind,
            transition.session.session_id,
        )
        for transition in transitions
    )

    assert result == (
        (
            SessionTransitionKind.DISCONNECTED,
            "session-b",
        ),
        (
            SessionTransitionKind.DISCONNECTED,
            "session-d",
        ),
        (
            SessionTransitionKind.CONNECTED,
            "session-a",
        ),
        (
            SessionTransitionKind.CONNECTED,
            "session-c",
        ),
    )
