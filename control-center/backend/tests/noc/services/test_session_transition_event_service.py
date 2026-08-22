from datetime import UTC, datetime

import pytest

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)

from app.noc.registry.registry import NodeRegistry
from app.noc.services.event_service import EventService
from app.noc.services.session_transition_detector import (
    SessionTransitionDetector,
    SessionTransitionKind,
)
from app.noc.services.session_transition_event_factory import (
    SessionTransitionEventFactory,
)
from app.noc.services.session_transition_event_service import (
    SessionTransitionEventResult,
    SessionTransitionEventService,
)


TIMESTAMP = datetime(
    2026,
    8,
    22,
    23,
    0,
    tzinfo=UTC,
)


def build_context():
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming-core",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    event_service = EventService(
        registry
    )

    service = SessionTransitionEventService(
        event_service=event_service,
    )

    return (
        node,
        instance,
        event_service,
        service,
    )


def build_session(
    *,
    session_id: str,
    protocol: SessionProtocol = SessionProtocol.SRT,
    path: str = "ejtv",
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=protocol,
        role=SessionRole.READER,
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


def test_constructor_builds_default_dependencies() -> None:
    _, _, event_service, service = build_context()

    assert service.event_service is event_service
    assert isinstance(
        service.detector,
        SessionTransitionDetector,
    )
    assert isinstance(
        service.factory,
        SessionTransitionEventFactory,
    )


def test_first_snapshot_establishes_baseline_without_events() -> None:
    node, instance, event_service, service = build_context()

    current = build_snapshot(
        build_session(session_id="session-a"),
        build_session(session_id="session-b"),
    )

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=None,
        current=current,
        timestamp=TIMESTAMP,
    )

    assert isinstance(
        result,
        SessionTransitionEventResult,
    )
    assert result.transitions == ()
    assert result.events == ()
    assert result.receipts == ()

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_connected_session_generates_event() -> None:
    node, instance, event_service, service = build_context()

    session_a = build_session(
        session_id="session-a",
    )

    session_b = build_session(
        session_id="session-b",
        protocol=SessionProtocol.RTSP,
        path="enlace",
    )

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=build_snapshot(session_a),
        current=build_snapshot(
            session_a,
            session_b,
        ),
        timestamp=TIMESTAMP,
    )

    assert len(result.transitions) == 1
    assert len(result.events) == 1
    assert len(result.receipts) == 1

    assert (
        result.transitions[0].kind
        is SessionTransitionKind.CONNECTED
    )

    event = result.events[0]

    assert event.event_type == "SESSION_CONNECTED"
    assert event.attributes["session_id"] == "session-b"
    assert event.attributes["protocol"] == "RTSP"
    assert event.attributes["path"] == "enlace"

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == (event,)


def test_disconnected_session_generates_event() -> None:
    node, instance, event_service, service = build_context()

    session_a = build_session(
        session_id="session-a",
    )

    session_b = build_session(
        session_id="session-b",
    )

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=build_snapshot(
            session_a,
            session_b,
        ),
        current=build_snapshot(
            session_a,
        ),
        timestamp=TIMESTAMP,
    )

    assert len(result.events) == 1

    assert (
        result.transitions[0].kind
        is SessionTransitionKind.DISCONNECTED
    )

    event = result.events[0]

    assert event.event_type == "SESSION_DISCONNECTED"
    assert event.attributes["session_id"] == "session-b"


def test_reconnection_same_address_generates_two_events() -> None:
    node, instance, event_service, service = build_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=build_snapshot(
            build_session(
                session_id="old-session",
            ),
        ),
        current=build_snapshot(
            build_session(
                session_id="new-session",
            ),
        ),
        timestamp=TIMESTAMP,
    )

    assert len(result.transitions) == 2
    assert len(result.events) == 2

    assert tuple(
        event.event_type
        for event in result.events
    ) == (
        "SESSION_DISCONNECTED",
        "SESSION_CONNECTED",
    )

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == result.events


def test_no_change_generates_no_event() -> None:
    node, instance, event_service, service = build_context()

    session = build_session(
        session_id="session-a",
    )

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=build_snapshot(session),
        current=build_snapshot(session),
        timestamp=TIMESTAMP,
    )

    assert result.transitions == ()
    assert result.events == ()
    assert result.receipts == ()

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()


@pytest.mark.parametrize(
    (
        "field_name",
        "value",
        "expected_message",
    ),
    (
        (
            "node_id",
            "invalid",
            "node_id must be a NodeId",
        ),
        (
            "instance_id",
            "invalid",
            "instance_id must be a NodeInstanceId",
        ),
        (
            "previous",
            "invalid",
            "previous must be a SessionSnapshot or None",
        ),
        (
            "current",
            "invalid",
            "current must be a SessionSnapshot",
        ),
        (
            "timestamp",
            "invalid",
            "timestamp must be a datetime",
        ),
    ),
)
def test_process_rejects_invalid_arguments(
    field_name,
    value,
    expected_message,
) -> None:
    node, instance, _, service = build_context()

    arguments = {
        "node_id": node.node_id,
        "instance_id": instance.instance_id,
        "previous": None,
        "current": build_snapshot(),
        "timestamp": TIMESTAMP,
    }

    arguments[field_name] = value

    with pytest.raises(
        TypeError,
        match=expected_message,
    ):
        service.process(
            **arguments,
        )


def test_process_transitions_persists_precomputed_transitions() -> None:
    node, instance, event_service, service = build_context()

    session = build_session(
        session_id="session-a",
    )

    transitions = (
        service.detector.detect(
            build_snapshot(),
            build_snapshot(session),
        )
    )

    result = service.process_transitions(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        transitions=transitions,
        timestamp=TIMESTAMP,
    )

    assert result.transitions == transitions
    assert len(result.events) == 1
    assert len(result.receipts) == 1

    assert (
        result.transitions[0].kind
        is SessionTransitionKind.CONNECTED
    )

    assert (
        result.events[0].event_type
        == "SESSION_CONNECTED"
    )

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == result.events


def test_process_transitions_accepts_empty_tuple() -> None:
    node, instance, event_service, service = build_context()

    result = service.process_transitions(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        transitions=(),
        timestamp=TIMESTAMP,
    )

    assert result.transitions == ()
    assert result.events == ()
    assert result.receipts == ()

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()
