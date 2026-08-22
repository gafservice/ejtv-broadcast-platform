from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.session_transition_detector import (
    SessionTransition,
    SessionTransitionKind,
)
from app.noc.services.session_transition_event_factory import (
    SessionTransitionEventFactory,
)


TIMESTAMP = datetime(
    2026,
    8,
    22,
    22,
    30,
    tzinfo=UTC,
)


def build_session(
    *,
    session_id: str = "session-001",
    protocol: SessionProtocol = SessionProtocol.SRT,
    role: SessionRole = SessionRole.READER,
    path: str | None = "ejtv",
    remote_ip: str = "201.192.154.132",
    remote_port: int | None = 50000,
    username: str | None = None,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
        role=role,
        state="read",
        remote_ip=remote_ip,
        remote_port=remote_port,
        path=path,
        connected_since=TIMESTAMP,
        username=username,
    )


def build_transition(
    *,
    kind: SessionTransitionKind,
    session: ActiveSession | None = None,
) -> SessionTransition:
    return SessionTransition(
        session=(
            session
            if session is not None
            else build_session()
        ),
        kind=kind,
    )


def test_create_connected_event() -> None:
    factory = SessionTransitionEventFactory()

    transition = build_transition(
        kind=SessionTransitionKind.CONNECTED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert isinstance(
        event,
        EventRecord,
    )

    assert event.event_type == "SESSION_CONNECTED"

    assert (
        event.severity
        is EventSeverity.INFO
    )

    assert event.timestamp == TIMESTAMP
    assert event.source == NodeInstanceId(
        "streaming-primary"
    )

    assert (
        event.title
        == "SRT reader connected on ejtv"
    )


def test_create_disconnected_event() -> None:
    factory = SessionTransitionEventFactory()

    transition = build_transition(
        kind=SessionTransitionKind.DISCONNECTED,
    )

    event = factory.create(
        transition=transition,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert (
        event.event_type
        == "SESSION_DISCONNECTED"
    )

    assert (
        event.severity
        is EventSeverity.NOTICE
    )

    assert (
        event.title
        == "SRT reader disconnected on ejtv"
    )


def test_event_contains_session_attributes() -> None:
    factory = SessionTransitionEventFactory()

    session = build_session(
        session_id="session-rtsp-001",
        protocol=SessionProtocol.RTSP,
        role=SessionRole.READER,
        path="enlace",
        remote_ip="201.192.154.132",
        remote_port=55947,
        username="viewer",
    )

    event = factory.create(
        transition=build_transition(
            kind=SessionTransitionKind.CONNECTED,
            session=session,
        ),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert event.attributes == {
        "session_id": "session-rtsp-001",
        "protocol": "RTSP",
        "role": "READER",
        "path": "enlace",
        "remote_ip": "201.192.154.132",
        "remote_port": "55947",
        "remote_address": "201.192.154.132:55947",
        "username": "viewer",
    }


def test_description_contains_operational_context() -> None:
    factory = SessionTransitionEventFactory()

    event = factory.create(
        transition=build_transition(
            kind=SessionTransitionKind.CONNECTED,
        ),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert "session-001" in event.description
    assert "201.192.154.132:50000" in event.description
    assert "ejtv" in event.description
    assert "SRT" in event.description
    assert "READER" in event.description


def test_event_id_is_generated() -> None:
    factory = SessionTransitionEventFactory()

    transition = build_transition(
        kind=SessionTransitionKind.CONNECTED,
    )

    first = factory.create(
        transition=transition,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    second = factory.create(
        transition=transition,
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert first.event_id.startswith(
        "evt-"
    )
    assert second.event_id.startswith(
        "evt-"
    )
    assert first.event_id != second.event_id


def test_path_none_is_supported() -> None:
    factory = SessionTransitionEventFactory()

    session = build_session(
        path=None,
    )

    event = factory.create(
        transition=build_transition(
            kind=SessionTransitionKind.CONNECTED,
            session=session,
        ),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert event.attributes["path"] == ""

    assert event.title == (
        "SRT reader connected on -"
    )


def test_remote_port_none_is_supported() -> None:
    factory = SessionTransitionEventFactory()

    session = build_session(
        remote_port=None,
    )

    event = factory.create(
        transition=build_transition(
            kind=SessionTransitionKind.CONNECTED,
            session=session,
        ),
        source=NodeInstanceId(
            "streaming-primary"
        ),
        timestamp=TIMESTAMP,
    )

    assert (
        event.attributes["remote_address"]
        == "201.192.154.132"
    )

    assert event.attributes["remote_port"] == ""


def test_create_rejects_invalid_transition() -> None:
    factory = SessionTransitionEventFactory()

    with pytest.raises(
        TypeError,
        match="transition must be a SessionTransition",
    ):
        factory.create(
            transition="invalid",  # type: ignore[arg-type]
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=TIMESTAMP,
        )


def test_create_rejects_invalid_source() -> None:
    factory = SessionTransitionEventFactory()

    with pytest.raises(
        TypeError,
        match="source must be a NodeInstanceId",
    ):
        factory.create(
            transition=build_transition(
                kind=SessionTransitionKind.CONNECTED,
            ),
            source="invalid",  # type: ignore[arg-type]
            timestamp=TIMESTAMP,
        )


def test_create_rejects_non_datetime_timestamp() -> None:
    factory = SessionTransitionEventFactory()

    with pytest.raises(
        TypeError,
        match="timestamp must be a datetime",
    ):
        factory.create(
            transition=build_transition(
                kind=SessionTransitionKind.CONNECTED,
            ),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp="invalid",  # type: ignore[arg-type]
        )


def test_create_rejects_naive_timestamp() -> None:
    factory = SessionTransitionEventFactory()

    with pytest.raises(
        ValueError,
        match="timezone-aware and UTC",
    ):
        factory.create(
            transition=build_transition(
                kind=SessionTransitionKind.CONNECTED,
            ),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=datetime(
                2026,
                8,
                22,
                22,
                30,
            ),
        )


def test_create_rejects_non_utc_timestamp() -> None:
    factory = SessionTransitionEventFactory()

    non_utc = timezone(
        timedelta(hours=-6)
    )

    with pytest.raises(
        ValueError,
        match="expressed in UTC",
    ):
        factory.create(
            transition=build_transition(
                kind=SessionTransitionKind.CONNECTED,
            ),
            source=NodeInstanceId(
                "streaming-primary"
            ),
            timestamp=datetime(
                2026,
                8,
                22,
                16,
                30,
                tzinfo=non_utc,
            ),
        )
