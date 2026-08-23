"""Integration tests for session operational runtime."""

from datetime import UTC, datetime, timedelta

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming.models import (
    MediaMTXSnapshot,
)
from app.noc.domain.critical_path_policy import CriticalPathPolicy
from app.noc.domain.expected_session_policy import ExpectedSessionPolicy
from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.runtime.session_alarm_runtime import (
    SessionAlarmRuntime,
)
from app.noc.runtime.session_operational_runtime import (
    SessionOperationalRuntime,
    SessionOperationalRuntimeResult,
)
from app.noc.services.alarm_service import AlarmService
from app.noc.services.critical_path_no_readers_alarm_service import (
    CriticalPathNoReadersAlarmService,
)
from app.noc.services.event_service import EventService
from app.noc.services.expected_session_alarm_service import (
    ExpectedSessionAlarmService,
)
from app.noc.services.reconnect_flapping_alarm_service import (
    ReconnectFlappingAlarmService,
)
from app.noc.services.session_transition_event_service import (
    SessionTransitionEventService,
)


TIMESTAMP = datetime(
    2026,
    8,
    23,
    5,
    0,
    tzinfo=UTC,
)


def build_context():
    registry = NodeRegistry(
        InMemoryNodeRepository()
    )

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    event_service = EventService(registry)
    alarm_service = AlarmService(registry)

    transition_event_service = (
        SessionTransitionEventService(
            event_service=event_service,
        )
    )

    alarm_runtime = SessionAlarmRuntime(
        expected_session_alarm_service=(
            ExpectedSessionAlarmService(
                alarm_service=alarm_service,
            )
        ),
        reconnect_flapping_alarm_service=(
            ReconnectFlappingAlarmService(
                alarm_service=alarm_service,
            )
        ),
        critical_path_alarm_service=(
            CriticalPathNoReadersAlarmService(
                alarm_service=alarm_service,
            )
        ),
        expected_session_policies=(
            ExpectedSessionPolicy(
                policy_id="expected-reader",
                protocol=SessionProtocol.SRT,
                role=SessionRole.READER,
                path="expected",
                missing_grace_period=timedelta(
                    seconds=15
                ),
            ),
        ),
        critical_path_policies=(
            CriticalPathPolicy(
                path="critical",
                no_readers_grace_period=timedelta(
                    seconds=15
                ),
            ),
        ),
    )

    runtime = SessionOperationalRuntime(
        transition_event_service=(
            transition_event_service
        ),
        alarm_runtime=alarm_runtime,
    )

    return (
        node,
        instance,
        event_service,
        alarm_service,
        runtime,
    )


def session(
    *,
    session_id: str,
    role: SessionRole,
    path: str,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=role,
        state=(
            "publish"
            if role is SessionRole.PUBLISHER
            else "read"
        ),
        remote_ip="201.192.154.132",
        remote_port=50000,
        path=path,
        connected_since=TIMESTAMP,
    )


def snapshot(
    *sessions: ActiveSession,
    captured_at: datetime = TIMESTAMP,
) -> SessionSnapshot:
    return SessionSnapshot(
        captured_at=captured_at,
        sessions=tuple(sessions),
    )


def media_snapshot(
    *,
    captured_at: datetime = TIMESTAMP,
) -> MediaMTXSnapshot:
    return MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )


def test_operational_runtime_shares_one_transition_set() -> None:
    (
        node,
        instance,
        event_service,
        _,
        runtime,
    ) = build_context()

    previous = snapshot(
        session(
            session_id="old-session",
            role=SessionRole.READER,
            path="flap",
        )
    )

    current = snapshot(
        session(
            session_id="new-session",
            role=SessionRole.READER,
            path="flap",
        )
    )

    result = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=previous,
        current=current,
        media_snapshot=media_snapshot(),
        timestamp=TIMESTAMP,
    )

    assert isinstance(
        result,
        SessionOperationalRuntimeResult,
    )

    assert len(result.transitions) == 2

    assert (
        result.event_result.transitions
        == result.transitions
    )

    assert len(
        result.alarm_result.reconnect_flapping_results
    ) == 2

    assert tuple(
        event.event_type
        for event in result.event_result.events
    ) == (
        "SESSION_DISCONNECTED",
        "SESSION_CONNECTED",
    )

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == result.event_result.events


def test_first_snapshot_is_baseline_for_transitions() -> None:
    (
        node,
        instance,
        event_service,
        _,
        runtime,
    ) = build_context()

    current = snapshot(
        session(
            session_id="existing-session",
            role=SessionRole.READER,
            path="flap",
        )
    )

    result = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=None,
        current=current,
        media_snapshot=media_snapshot(),
        timestamp=TIMESTAMP,
    )

    assert result.transitions == ()
    assert result.event_result.events == ()

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()
