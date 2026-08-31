"""Integration tests for multimedia session alarm runtime."""

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
    StreamingPathMeasurement,
)
from app.domain.streaming.models import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaReader,
    MediaSource,
)
from app.noc.domain.critical_path_policy import (
    CriticalPathPolicy,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
)
from app.noc.domain.node import Node
from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.domain.reconnect_flapping_policy import (
    ReconnectFlappingPolicy,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.runtime.session_alarm_runtime import (
    SessionAlarmRuntime,
    SessionAlarmRuntimeResult,
)
from app.noc.services.alarm_service import AlarmService
from app.noc.services.critical_path_no_readers_alarm_service import (
    CriticalPathNoReadersAlarmService,
)
from app.noc.services.critical_path_unavailable_alarm_service import (
    CriticalPathUnavailableAlarmService,
)
from app.noc.services.critical_path_traffic_stalled_alarm_service import (
    CriticalPathTrafficStalledAlarmService,
)
from app.noc.services.expected_session_alarm_service import (
    ExpectedSessionAlarmService,
)
from app.noc.services.reconnect_flapping_alarm_service import (
    ReconnectFlappingAlarmService,
)
from app.noc.services.reconnect_flapping_evaluator import (
    ReconnectFlappingEvaluator,
)
from app.noc.services.session_transition_detector import (
    SessionTransition,
    SessionTransitionKind,
)


BASE_TIME = datetime(
    2026,
    8,
    23,
    4,
    30,
    tzinfo=UTC,
)


class MemoryRepository:
    def __init__(self):
        self.nodes = {}

    def save(self, node):
        self.nodes[node.node_id.id] = node

    def get(self, node_id):
        return self.nodes.get(node_id.id)

    def exists(self, node_id):
        return node_id.id in self.nodes

    def list_all(self):
        return tuple(self.nodes.values())

    def delete(self, node_id):
        return self.nodes.pop(
            node_id.id,
            None,
        ) is not None

    def count(self):
        return len(self.nodes)


def make_context():
    repository = MemoryRepository()
    registry = NodeRegistry(repository)

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

    alarm_service = AlarmService(registry)

    runtime = SessionAlarmRuntime(
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
        reconnect_flapping_evaluator=(
            ReconnectFlappingEvaluator(
                policy=ReconnectFlappingPolicy(
                    reconnect_timeout=timedelta(
                        seconds=10
                    ),
                    window=timedelta(
                        seconds=30
                    ),
                    threshold=2,
                )
            )
        ),
    )

    return (
        node,
        instance,
        alarm_service,
        runtime,
    )


def build_session(
    *,
    session_id: str,
    role: SessionRole,
    path: str,
    remote_ip: str = "201.192.154.132",
    remote_port: int = 50000,
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
        remote_ip=remote_ip,
        remote_port=remote_port,
        path=path,
        connected_since=BASE_TIME,
    )


def build_snapshot(
    *,
    captured_at: datetime,
    sessions: tuple[ActiveSession, ...],
) -> SessionSnapshot:
    return SessionSnapshot(
        captured_at=captured_at,
        sessions=sessions,
    )


def build_media_path(
    *,
    reader_count: int = 0,
) -> MediaPath:
    return MediaPath(
        name="critical",
        configuration_name="critical",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        source=MediaSource(
            source_type="mpegtsSource",
            source_id="critical-source",
        ),
        readers=tuple(
            MediaReader(
                reader_type="srtConn",
                reader_id=f"critical-reader-{index}",
            )
            for index in range(reader_count)
        ),
    )


def build_media_snapshot(
    *,
    captured_at: datetime,
    reader_count: int = 0,
) -> MediaMTXSnapshot:
    return MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(
            build_media_path(
                reader_count=reader_count,
            ),
        ),
        reported_item_count=1,
        reported_page_count=1,
    )


def build_streaming_measurement(
    *,
    captured_at: datetime = BASE_TIME,
) -> StreamingMeasurement:
    """Build a baseline measurement with no reliable traffic rate yet."""

    return StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )


def build_available_streaming_measurement(
    *,
    captured_at: datetime,
    inbound_bitrate_bps: float,
    reader_count: int = 1,
) -> StreamingMeasurement:
    """Build one reliable traffic measurement for the critical path."""

    previous_captured_at = (
        captured_at - timedelta(seconds=1)
    )

    path_measurement = StreamingPathMeasurement(
        name="critical",
        status=MediaPathStatus.ACTIVE,
        previous_status=MediaPathStatus.ACTIVE,
        reader_count=reader_count,
        reader_delta=0,
        inbound_delta_bytes=0,
        outbound_delta_bytes=0,
        inbound_bitrate_bps=inbound_bitrate_bps,
        outbound_bitrate_bps=0.0,
        state_changed=False,
        quality=MeasurementQuality.AVAILABLE,
    )

    return StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=previous_captured_at,
        interval_seconds=1.0,
        paths=(path_measurement,),
        total_inbound_bitrate_bps=inbound_bitrate_bps,
        total_outbound_bitrate_bps=0.0,
        quality=MeasurementQuality.AVAILABLE,
    )


def build_transition(
    *,
    kind: SessionTransitionKind,
    session_id: str,
    remote_port: int,
) -> SessionTransition:
    return SessionTransition(
        session=build_session(
            session_id=session_id,
            role=SessionRole.READER,
            path="flap",
            remote_ip="203.0.113.10",
            remote_port=remote_port,
        ),
        kind=kind,
    )


def active_alarm_types(
    alarm_service,
    node,
    instance,
) -> set[str]:
    return {
        alarm.alarm_type
        for alarm in alarm_service.active(
            node.node_id,
            instance.instance_id,
        )
    }


def test_all_session_alarm_policies_coexist_and_recover() -> None:
    (
        node,
        instance,
        alarm_service,
        runtime,
    ) = make_context()

    critical_publisher = build_session(
        session_id="critical-publisher",
        role=SessionRole.PUBLISHER,
        path="critical",
    )

    #
    # t=0
    #
    # - expected reader is absent;
    # - critical publisher exists with zero readers;
    # - both temporal grace periods begin.
    #
    first = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME,
            sessions=(
                critical_publisher,
            ),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=BASE_TIME,
            reader_count=0,
        ),
        streaming_measurement=build_streaming_measurement(),
        transitions=(),
        timestamp=BASE_TIME,
    )

    assert isinstance(
        first,
        SessionAlarmRuntimeResult,
    )

    assert len(
        first.expected_session_results
    ) == 1

    assert len(
        first.critical_path_results
    ) == 1

    assert (
        first.reconnect_flapping_results
        == ()
    )

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()

    #
    # t=15
    #
    # Both grace periods expire.
    #
    runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=(
                BASE_TIME
                + timedelta(seconds=15)
            ),
            sessions=(
                critical_publisher,
            ),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=(
                BASE_TIME
                + timedelta(seconds=15)
            ),
            reader_count=0,
        ),
        streaming_measurement=build_streaming_measurement(),
        transitions=(),
        timestamp=(
            BASE_TIME
            + timedelta(seconds=15)
        ),
    )

    assert active_alarm_types(
        alarm_service,
        node,
        instance,
    ) == {
        "EXPECTED_SESSION_MISSING",
        "CRITICAL_PATH_NO_READERS",
    }

    #
    # t=20
    #
    # First reconnect for an independent logical session.
    #
    first_reconnect = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=(
                BASE_TIME
                + timedelta(seconds=20)
            ),
            sessions=(
                critical_publisher,
            ),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=(
                BASE_TIME
                + timedelta(seconds=20)
            ),
            reader_count=0,
        ),
        streaming_measurement=build_streaming_measurement(),
        transitions=(
            build_transition(
                kind=SessionTransitionKind.DISCONNECTED,
                session_id="flap-old-1",
                remote_port=51000,
            ),
            build_transition(
                kind=SessionTransitionKind.CONNECTED,
                session_id="flap-new-1",
                remote_port=52000,
            ),
        ),
        timestamp=(
            BASE_TIME
            + timedelta(seconds=20)
        ),
    )

    assert len(
        first_reconnect.reconnect_flapping_results
    ) == 2

    assert active_alarm_types(
        alarm_service,
        node,
        instance,
    ) == {
        "EXPECTED_SESSION_MISSING",
        "CRITICAL_PATH_NO_READERS",
    }

    #
    # t=25
    #
    # Second reconnect reaches flapping threshold.
    #
    runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=(
                BASE_TIME
                + timedelta(seconds=25)
            ),
            sessions=(
                critical_publisher,
            ),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=(
                BASE_TIME
                + timedelta(seconds=25)
            ),
            reader_count=0,
        ),
        streaming_measurement=build_streaming_measurement(),
        transitions=(
            build_transition(
                kind=SessionTransitionKind.DISCONNECTED,
                session_id="flap-old-2",
                remote_port=53000,
            ),
            build_transition(
                kind=SessionTransitionKind.CONNECTED,
                session_id="flap-new-2",
                remote_port=54000,
            ),
        ),
        timestamp=(
            BASE_TIME
            + timedelta(seconds=25)
        ),
    )

    assert active_alarm_types(
        alarm_service,
        node,
        instance,
    ) == {
        "EXPECTED_SESSION_MISSING",
        "CRITICAL_PATH_NO_READERS",
        "RECONNECT_FLAPPING",
    }

    #
    # t=31
    #
    # Expected reader appears and the critical path gains a reader.
    # Flapping remains active because reconnects are still inside window.
    #
    expected_reader = build_session(
        session_id="expected-reader-1",
        role=SessionRole.READER,
        path="expected",
    )

    critical_reader = build_session(
        session_id="critical-reader-1",
        role=SessionRole.READER,
        path="critical",
    )

    recovered_snapshot = build_snapshot(
        captured_at=(
            BASE_TIME
            + timedelta(seconds=31)
        ),
        sessions=(
            critical_publisher,
            critical_reader,
            expected_reader,
        ),
    )

    runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=recovered_snapshot,
        media_snapshot=build_media_snapshot(
            captured_at=(
                BASE_TIME
                + timedelta(seconds=31)
            ),
            reader_count=1,
        ),
        streaming_measurement=build_streaming_measurement(),
        transitions=(),
        timestamp=(
            BASE_TIME
            + timedelta(seconds=31)
        ),
    )

    assert active_alarm_types(
        alarm_service,
        node,
        instance,
    ) == {
        "RECONNECT_FLAPPING",
    }

    #
    # t=56
    #
    # No new reconnect transitions occur. The reconnect history ages
    # outside the 30-second window and the flapping alarm resolves.
    #
    final_result = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=(
                BASE_TIME
                + timedelta(seconds=56)
            ),
            sessions=(
                critical_publisher,
                critical_reader,
                expected_reader,
            ),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=(
                BASE_TIME
                + timedelta(seconds=56)
            ),
            reader_count=1,
        ),
        streaming_measurement=build_streaming_measurement(),
        transitions=(),
        timestamp=(
            BASE_TIME
            + timedelta(seconds=56)
        ),
    )

    assert len(
        final_result.reconnect_flapping_results
    ) == 1

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_reconnect_flapping_may_be_disabled() -> None:
    (
        node,
        instance,
        alarm_service,
        _,
    ) = make_context()

    runtime = SessionAlarmRuntime(
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
        reconnect_flapping_enabled=False,
    )

    result = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME,
            sessions=(),
        ),
        media_snapshot=MediaMTXSnapshot(
            captured_at=BASE_TIME,
            paths=(),
            reported_item_count=0,
            reported_page_count=0,
        ),
        streaming_measurement=build_streaming_measurement(),
        transitions=(
            build_transition(
                kind=SessionTransitionKind.DISCONNECTED,
                session_id="old-session",
                remote_port=51000,
            ),
            build_transition(
                kind=SessionTransitionKind.CONNECTED,
                session_id="new-session",
                remote_port=52000,
            ),
        ),
        timestamp=BASE_TIME,
    )

    assert result.reconnect_flapping_results == ()
    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_critical_path_unavailable_runtime_lifecycle() -> None:
    (
        node,
        instance,
        alarm_service,
        runtime,
    ) = make_context()

    healthy_media = build_media_snapshot(
        captured_at=BASE_TIME,
        reader_count=1,
    )

    first = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME,
            sessions=(),
        ),
        media_snapshot=healthy_media,
        streaming_measurement=build_streaming_measurement(),
        transitions=(),
        timestamp=BASE_TIME,
    )

    assert len(
        first.critical_path_unavailable_results
    ) == 1

    assert (
        first.critical_path_unavailable_results[0]
        .stabilization
        .confirmed_unavailable
        is False
    )

    #
    # Path disappears at t=5.
    #
    missing_media_5 = MediaMTXSnapshot(
        captured_at=BASE_TIME + timedelta(seconds=5),
        paths=(),
        reported_item_count=0,
        reported_page_count=1,
    )

    second = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=5),
            sessions=(),
        ),
        media_snapshot=missing_media_5,
        streaming_measurement=build_streaming_measurement(),
        transitions=(),
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    unavailable_result = (
        second.critical_path_unavailable_results[0]
    )

    assert (
        unavailable_result
        .stabilization
        .confirmed_unavailable
        is False
    )

    assert unavailable_result.alarm is None

    #
    # t=20 -> 15 continuous seconds unavailable.
    #
    missing_media_20 = MediaMTXSnapshot(
        captured_at=BASE_TIME + timedelta(seconds=20),
        paths=(),
        reported_item_count=0,
        reported_page_count=1,
    )

    third = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=20),
            sessions=(),
        ),
        media_snapshot=missing_media_20,
        streaming_measurement=build_streaming_measurement(),
        transitions=(),
        timestamp=BASE_TIME + timedelta(seconds=20),
    )

    alarm_result = (
        third.critical_path_unavailable_results[0]
    )

    assert (
        alarm_result
        .stabilization
        .confirmed_unavailable
        is True
    )

    assert alarm_result.alarm is not None
    assert (
        alarm_result.alarm.alarm_type
        == "CRITICAL_PATH_UNAVAILABLE"
    )
    assert (
        alarm_result.alarm.state
        is AlarmState.ACTIVE
    )

    raised_alarm_id = alarm_result.alarm.alarm_id

    assert "CRITICAL_PATH_UNAVAILABLE" in (
        active_alarm_types(
            alarm_service,
            node,
            instance,
        )
    )

    #
    # t=25 -> path returns healthy.
    #
    recovered = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=25),
            sessions=(),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=25),
            reader_count=1,
        ),
        streaming_measurement=build_streaming_measurement(),
        transitions=(),
        timestamp=BASE_TIME + timedelta(seconds=25),
    )

    recovered_result = (
        recovered.critical_path_unavailable_results[0]
    )

    assert recovered_result.alarm is not None
    assert (
        recovered_result.alarm.state
        is AlarmState.RESOLVED
    )
    assert (
        recovered_result.alarm.alarm_id
        == raised_alarm_id
    )

    assert "CRITICAL_PATH_UNAVAILABLE" not in (
        active_alarm_types(
            alarm_service,
            node,
            instance,
        )
    )

def test_critical_path_traffic_stalled_runtime_lifecycle() -> None:
    (
        node,
        instance,
        alarm_service,
        runtime,
    ) = make_context()

    #
    # t=0 -> healthy inbound traffic.
    #
    first = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME,
            sessions=(),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=BASE_TIME,
            reader_count=1,
        ),
        streaming_measurement=(
            build_available_streaming_measurement(
                captured_at=BASE_TIME,
                inbound_bitrate_bps=4_500_000.0,
            )
        ),
        transitions=(),
        timestamp=BASE_TIME,
    )

    assert len(
        first.critical_path_traffic_stalled_results
    ) == 1

    healthy_result = (
        first.critical_path_traffic_stalled_results[0]
    )

    assert (
        healthy_result.stabilization.confirmed_stalled
        is False
    )
    assert healthy_result.alarm is None

    assert "CRITICAL_PATH_TRAFFIC_STALLED" not in (
        active_alarm_types(
            alarm_service,
            node,
            instance,
        )
    )

    #
    # t=5 -> inbound traffic stops.
    # Grace period begins.
    #
    stalled_5 = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=5),
            sessions=(),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=5),
            reader_count=1,
        ),
        streaming_measurement=(
            build_available_streaming_measurement(
                captured_at=BASE_TIME + timedelta(seconds=5),
                inbound_bitrate_bps=0.0,
            )
        ),
        transitions=(),
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    stalled_result_5 = (
        stalled_5.critical_path_traffic_stalled_results[0]
    )

    assert (
        stalled_result_5.stabilization.confirmed_stalled
        is False
    )
    assert stalled_result_5.alarm is None

    #
    # t=19 -> only 14 continuous seconds stalled.
    #
    stalled_19 = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=19),
            sessions=(),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=19),
            reader_count=1,
        ),
        streaming_measurement=(
            build_available_streaming_measurement(
                captured_at=BASE_TIME + timedelta(seconds=19),
                inbound_bitrate_bps=0.0,
            )
        ),
        transitions=(),
        timestamp=BASE_TIME + timedelta(seconds=19),
    )

    assert (
        stalled_19
        .critical_path_traffic_stalled_results[0]
        .stabilization
        .confirmed_stalled
        is False
    )

    #
    # t=20 -> exactly 15 continuous seconds stalled.
    #
    stalled_20 = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=20),
            sessions=(),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=20),
            reader_count=1,
        ),
        streaming_measurement=(
            build_available_streaming_measurement(
                captured_at=BASE_TIME + timedelta(seconds=20),
                inbound_bitrate_bps=0.0,
            )
        ),
        transitions=(),
        timestamp=BASE_TIME + timedelta(seconds=20),
    )

    alarm_result = (
        stalled_20.critical_path_traffic_stalled_results[0]
    )

    assert (
        alarm_result.stabilization.confirmed_stalled
        is True
    )
    assert alarm_result.alarm is not None
    assert (
        alarm_result.alarm.alarm_type
        == "CRITICAL_PATH_TRAFFIC_STALLED"
    )
    assert alarm_result.alarm.state is AlarmState.ACTIVE

    raised_alarm_id = alarm_result.alarm.alarm_id

    assert "CRITICAL_PATH_TRAFFIC_STALLED" in (
        active_alarm_types(
            alarm_service,
            node,
            instance,
        )
    )

    #
    # t=30 -> still stalled; same alarm, no duplicate.
    #
    stalled_30 = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=30),
            sessions=(),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=30),
            reader_count=1,
        ),
        streaming_measurement=(
            build_available_streaming_measurement(
                captured_at=BASE_TIME + timedelta(seconds=30),
                inbound_bitrate_bps=0.0,
            )
        ),
        transitions=(),
        timestamp=BASE_TIME + timedelta(seconds=30),
    )

    persistent_result = (
        stalled_30.critical_path_traffic_stalled_results[0]
    )

    assert persistent_result.alarm is not None
    assert (
        persistent_result.alarm.alarm_id
        == raised_alarm_id
    )

    active_traffic_alarms = tuple(
        alarm
        for alarm in alarm_service.active(
            node.node_id,
            instance.instance_id,
        )
        if (
            alarm.alarm_type
            == "CRITICAL_PATH_TRAFFIC_STALLED"
        )
    )

    assert len(active_traffic_alarms) == 1

    #
    # t=35 -> positive inbound traffic proves recovery.
    #
    recovered = runtime.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        session_snapshot=build_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=35),
            sessions=(),
        ),
        media_snapshot=build_media_snapshot(
            captured_at=BASE_TIME + timedelta(seconds=35),
            reader_count=1,
        ),
        streaming_measurement=(
            build_available_streaming_measurement(
                captured_at=BASE_TIME + timedelta(seconds=35),
                inbound_bitrate_bps=4_600_000.0,
            )
        ),
        transitions=(),
        timestamp=BASE_TIME + timedelta(seconds=35),
    )

    recovered_result = (
        recovered.critical_path_traffic_stalled_results[0]
    )

    assert recovered_result.alarm is not None
    assert (
        recovered_result.alarm.alarm_id
        == raised_alarm_id
    )
    assert (
        recovered_result.alarm.state
        is AlarmState.RESOLVED
    )

    assert "CRITICAL_PATH_TRAFFIC_STALLED" not in (
        active_alarm_types(
            alarm_service,
            node,
            instance,
        )
    )
