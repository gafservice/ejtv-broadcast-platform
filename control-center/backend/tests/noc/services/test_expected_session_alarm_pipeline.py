"""End-to-end expected multimedia session alarm pipeline tests."""

from datetime import datetime, timedelta, timezone

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.noc.domain.expected_session_policy import (
    ExpectedSessionPolicy,
)
from app.noc.domain.node import Node
from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_service import (
    AlarmDisposition,
    AlarmService,
)
from app.noc.services.expected_session_alarm_service import (
    ExpectedSessionAlarmService,
)
from app.noc.services.expected_session_evaluator import (
    ExpectedSessionEvaluator,
    ExpectedSessionState,
)
from app.noc.services.expected_session_stabilizer import (
    ExpectedSessionStabilizer,
)


BASE_TIME = datetime(
    2026,
    8,
    23,
    0,
    30,
    tzinfo=timezone.utc,
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

    return (
        node,
        instance,
        alarm_service,
        ExpectedSessionEvaluator(),
        ExpectedSessionStabilizer(),
        ExpectedSessionAlarmService(
            alarm_service=alarm_service,
        ),
    )


def build_policy() -> ExpectedSessionPolicy:
    return ExpectedSessionPolicy(
        policy_id="ejtv-srt-reader",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path="ejtv",
        missing_grace_period=timedelta(
            seconds=15
        ),
    )


def build_session(
    *,
    session_id: str = "session-001",
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="read",
        remote_ip="201.192.154.132",
        remote_port=50000,
        path="ejtv",
        connected_since=BASE_TIME,
    )


def build_snapshot(
    *,
    captured_at: datetime,
    sessions: tuple[ActiveSession, ...] = (),
) -> SessionSnapshot:
    return SessionSnapshot(
        captured_at=captured_at,
        sessions=sessions,
    )


def process_cycle(
    *,
    evaluator,
    stabilizer,
    alarm_service,
    node,
    instance,
    policy,
    timestamp,
    sessions=(),
):
    snapshot = build_snapshot(
        captured_at=timestamp,
        sessions=sessions,
    )

    evaluations = evaluator.evaluate(
        snapshot=snapshot,
        policies=(policy,),
    )

    assert len(evaluations) == 1

    stabilization = stabilizer.stabilize(
        evaluation=evaluations[0],
        observed_at=timestamp,
    )

    result = alarm_service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        stabilization=stabilization,
        timestamp=timestamp,
    )

    return (
        evaluations[0],
        stabilization,
        result,
    )


def test_expected_session_missing_full_lifecycle() -> None:
    (
        node,
        instance,
        alarm_registry,
        evaluator,
        stabilizer,
        alarm_service,
    ) = make_context()

    policy = build_policy()

    # t=0: first missing observation starts grace period.
    evaluation_0, stabilization_0, result_0 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_service=alarm_service,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME,
    )

    assert (
        evaluation_0.state
        is ExpectedSessionState.MISSING
    )
    assert stabilization_0.confirmed_missing is False
    assert result_0.alarm is None
    assert result_0.receipt is None

    # t=14: still inside grace period.
    _, stabilization_14, result_14 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_service=alarm_service,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=14),
    )

    assert stabilization_14.confirmed_missing is False
    assert result_14.alarm is None
    assert result_14.receipt is None

    # t=15: missing condition becomes confirmed.
    _, stabilization_15, result_15 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_service=alarm_service,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=15),
    )

    assert stabilization_15.confirmed_missing is True
    assert result_15.alarm is not None
    assert result_15.receipt is not None

    assert result_15.receipt.disposition is (
        AlarmDisposition.RAISED
    )

    assert result_15.alarm.state is AlarmState.ACTIVE

    raised_alarm_id = result_15.alarm.alarm_id

    # t=30: still missing, but no duplicate alarm.
    _, stabilization_30, result_30 = process_cycle(
        evaluator=evaluator,
        stabilizer=stabilizer,
        alarm_service=alarm_service,
        node=node,
        instance=instance,
        policy=policy,
        timestamp=BASE_TIME + timedelta(seconds=30),
    )

    assert stabilization_30.confirmed_missing is True
    assert result_30.alarm is not None
    assert result_30.alarm.alarm_id == raised_alarm_id
    assert result_30.receipt is None

    active = alarm_registry.active(
        node.node_id,
        instance.instance_id,
    )

    assert len(active) == 1
    assert active[0].alarm_id == raised_alarm_id

    # t=45: expected session returns.
    recovered_session = build_session(
        session_id="session-reconnected",
    )

    evaluation_45, stabilization_45, result_45 = (
        process_cycle(
            evaluator=evaluator,
            stabilizer=stabilizer,
            alarm_service=alarm_service,
            node=node,
            instance=instance,
            policy=policy,
            timestamp=BASE_TIME + timedelta(seconds=45),
            sessions=(recovered_session,),
        )
    )

    assert (
        evaluation_45.state
        is ExpectedSessionState.PRESENT
    )
    assert stabilization_45.missing_since is None
    assert stabilization_45.confirmed_missing is False

    assert result_45.alarm is not None
    assert result_45.receipt is not None

    assert result_45.receipt.disposition is (
        AlarmDisposition.RESOLVED
    )

    assert result_45.alarm.state is AlarmState.RESOLVED
    assert result_45.alarm.alarm_id == raised_alarm_id

    assert alarm_registry.active(
        node.node_id,
        instance.instance_id,
    ) == ()
