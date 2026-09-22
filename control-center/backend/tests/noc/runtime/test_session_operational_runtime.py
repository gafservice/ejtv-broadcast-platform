"""Integration tests for session operational runtime."""

from datetime import UTC, datetime, timedelta

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming.metrics import (
    MeasurementQuality,
    StreamingMeasurement,
)
from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaReader,
    MediaSource,
)
from app.noc.domain.critical_path_policy import CriticalPathPolicy
from app.noc.domain.expected_session_policy import ExpectedSessionPolicy
from app.noc.services.expected_session_evaluator import ExpectedSessionState
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
from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderState,
)
from app.noc.services.critical_path_no_readers_alarm_service import (
    CriticalPathNoReadersAlarmService,
)
from app.noc.services.critical_path_unavailable_alarm_service import (
    CriticalPathUnavailableAlarmService,
)
from app.noc.services.critical_path_traffic_stalled_alarm_service import (
    CriticalPathTrafficStalledAlarmService,
)
from app.noc.services.event_service import EventService
from app.noc.services.expected_session_alarm_service import (
    ExpectedSessionAlarmService,
)
from app.noc.services.reconnect_flapping_alarm_service import (
    ReconnectFlappingAlarmService,
)
from app.noc.services.session_operational_projector import (
    SessionOperationalProjector,
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
        critical_path_unavailable_alarm_service=(
            CriticalPathUnavailableAlarmService(
                alarm_service=alarm_service,
            )
        ),
        critical_path_traffic_stalled_alarm_service=(
            CriticalPathTrafficStalledAlarmService(
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
        operational_projector=SessionOperationalProjector(
            internal_observer_user_agent="EBP-MediaObserver/1",
        ),
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


def streaming_measurement(
    *,
    captured_at: datetime = TIMESTAMP,
) -> StreamingMeasurement:
    """Build the initial no-rate baseline measurement."""

    return StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
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
        streaming_measurement=streaming_measurement(),
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
        streaming_measurement=streaming_measurement(),
        timestamp=TIMESTAMP,
    )

    assert result.transitions == ()
    assert result.event_result.events == ()

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_internal_observer_is_not_operational_client_or_reader_demand() -> None:
    (
        node,
        instance,
        event_service,
        _,
        runtime,
    ) = build_context()

    previous = snapshot()

    internal_observer = ActiveSession(
        session_id="internal-observer",
        protocol=SessionProtocol.RTSP,
        role=SessionRole.READER,
        state="read",
        remote_ip="127.0.0.1",
        remote_port=50000,
        path="critical",
        connected_since=TIMESTAMP,
        user_agent="EBP-MediaObserver/1",
    )

    current = snapshot(
        internal_observer,
    )

    critical_path = MediaPath(
        name="critical",
        configuration_name="critical",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="srtSource",
        ),
        readers=(
            MediaReader(
                reader_type="rtspSession",
                reader_id="internal-observer",
            ),
        ),
    )

    raw_media_snapshot = MediaMTXSnapshot(
        captured_at=TIMESTAMP,
        paths=(critical_path,),
        reported_item_count=1,
        reported_page_count=1,
    )

    result = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=previous,
        current=current,
        media_snapshot=raw_media_snapshot,
        streaming_measurement=streaming_measurement(),
        timestamp=TIMESTAMP,
    )

    assert result.transitions == ()
    assert result.event_result.events == ()

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()

    assert len(
        result.alarm_result.critical_path_results
    ) == 1

    assert (
        result.alarm_result
        .critical_path_results[0]
        .stabilization
        .evaluation
        .state
        is CriticalPathReaderState.NO_READERS
    )

    assert critical_path.reader_count == 1


def test_internal_observer_disconnect_is_not_operational_transition() -> None:
    (
        node,
        instance,
        event_service,
        _,
        runtime,
    ) = build_context()

    internal_observer = ActiveSession(
        session_id="internal-observer-disconnect",
        protocol=SessionProtocol.RTSP,
        role=SessionRole.READER,
        state="read",
        remote_ip="127.0.0.1",
        remote_port=50000,
        path="critical",
        connected_since=TIMESTAMP,
        user_agent="EBP-MediaObserver/1",
    )

    previous = snapshot(
        internal_observer,
    )

    current = snapshot()

    result = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=previous,
        current=current,
        media_snapshot=media_snapshot(),
        streaming_measurement=streaming_measurement(),
        timestamp=TIMESTAMP,
    )

    assert result.transitions == ()
    assert result.event_result.transitions == ()
    assert result.event_result.events == ()
    assert result.event_result.receipts == ()

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_internal_observer_does_not_satisfy_expected_session_policy() -> None:
    (
        node,
        instance,
        event_service,
        _,
        runtime,
    ) = build_context()

    internal_observer = ActiveSession(
        session_id="internal-observer-expected",
        protocol=SessionProtocol.RTSP,
        role=SessionRole.READER,
        state="read",
        remote_ip="127.0.0.1",
        remote_port=50000,
        path="critical",
        connected_since=TIMESTAMP,
        user_agent="EBP-MediaObserver/1",
    )

    runtime._alarm_runtime._expected_session_policies = (
        ExpectedSessionPolicy(
            policy_id="internal-must-not-satisfy",
            protocol=SessionProtocol.RTSP,
            role=SessionRole.READER,
            path="critical",
            missing_grace_period=timedelta(seconds=0),
        ),
    )

    result = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=snapshot(),
        current=snapshot(
            internal_observer,
        ),
        media_snapshot=media_snapshot(),
        streaming_measurement=streaming_measurement(),
        timestamp=TIMESTAMP,
    )

    assert result.transitions == ()
    assert result.event_result.events == ()

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()

    assert len(
        result.alarm_result.expected_session_results
    ) == 1

    expected_result = (
        result.alarm_result.expected_session_results[0]
    )

    assert (
        expected_result.stabilization.evaluation.state
        is ExpectedSessionState.MISSING
    )

    assert (
        expected_result.stabilization.evaluation.matching_sessions
        == ()
    )
