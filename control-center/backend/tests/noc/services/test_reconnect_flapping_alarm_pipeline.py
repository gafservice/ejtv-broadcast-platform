"""End-to-end reconnect flapping alarm pipeline tests."""

from datetime import datetime, timedelta, timezone

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.node import Node
from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.domain.reconnect_flapping_policy import (
    ReconnectFlappingPolicy,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_service import (
    AlarmDisposition,
    AlarmService,
)
from app.noc.services.reconnect_flapping_alarm_service import (
    ReconnectFlappingAlarmService,
)
from app.noc.services.reconnect_flapping_evaluator import (
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
    2,
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

    evaluator = ReconnectFlappingEvaluator(
        policy=ReconnectFlappingPolicy(
            reconnect_timeout=timedelta(seconds=10),
            window=timedelta(seconds=30),
            threshold=3,
        )
    )

    alarm_coordinator = ReconnectFlappingAlarmService(
        alarm_service=alarm_service,
    )

    return (
        node,
        instance,
        alarm_service,
        evaluator,
        alarm_coordinator,
    )


def build_session(
    *,
    session_id: str,
    remote_port: int,
) -> ActiveSession:
    return ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="read",
        remote_ip="201.192.154.132",
        remote_port=remote_port,
        path="ejtv",
        connected_since=BASE_TIME,
    )


def transition(
    *,
    kind: SessionTransitionKind,
    session_id: str,
    remote_port: int,
) -> SessionTransition:
    return SessionTransition(
        session=build_session(
            session_id=session_id,
            remote_port=remote_port,
        ),
        kind=kind,
    )


def test_reconnect_flapping_full_lifecycle() -> None:
    (
        node,
        instance,
        alarm_service,
        evaluator,
        alarm_coordinator,
    ) = make_context()

    reconnect_pairs = (
        (0, 1),
        (10, 11),
        (20, 21),
    )

    raised_alarm_id = None
    last_evaluation = None

    for index, (
        disconnect_second,
        connect_second,
    ) in enumerate(reconnect_pairs):
        disconnected = evaluator.evaluate(
            transition=transition(
                kind=SessionTransitionKind.DISCONNECTED,
                session_id=f"old-{index}",
                remote_port=50000 + index,
            ),
            observed_at=(
                BASE_TIME
                + timedelta(seconds=disconnect_second)
            ),
        )

        disconnect_alarm_result = alarm_coordinator.process(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            evaluation=disconnected,
            timestamp=(
                BASE_TIME
                + timedelta(seconds=disconnect_second)
            ),
        )

        assert disconnect_alarm_result.receipt is None

        connected = evaluator.evaluate(
            transition=transition(
                kind=SessionTransitionKind.CONNECTED,
                session_id=f"new-{index}",
                remote_port=51000 + index,
            ),
            observed_at=(
                BASE_TIME
                + timedelta(seconds=connect_second)
            ),
        )

        last_evaluation = connected

        alarm_result = alarm_coordinator.process(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            evaluation=connected,
            timestamp=(
                BASE_TIME
                + timedelta(seconds=connect_second)
            ),
        )

        if index < 2:
            assert (
                connected.state
                is ReconnectFlappingState.STABLE
            )
            assert alarm_result.alarm is None
            assert alarm_result.receipt is None
        else:
            assert (
                connected.state
                is ReconnectFlappingState.FLAPPING
            )

            assert alarm_result.alarm is not None
            assert alarm_result.receipt is not None
            assert alarm_result.receipt.disposition is (
                AlarmDisposition.RAISED
            )
            assert (
                alarm_result.alarm.state
                is AlarmState.ACTIVE
            )

            raised_alarm_id = alarm_result.alarm.alarm_id

    assert last_evaluation is not None
    assert raised_alarm_id is not None

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert len(active) == 1
    assert active[0].alarm_id == raised_alarm_id

    # No new transition occurs. Time alone ages reconnects
    # outside the flapping window.
    stable = evaluator.observe(
        identity=last_evaluation.identity,
        observed_at=BASE_TIME + timedelta(seconds=52),
    )

    assert stable.state is ReconnectFlappingState.STABLE
    assert stable.reconnect_count == 0
    assert stable.reconnect_detected is False

    recovered = alarm_coordinator.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=stable,
        timestamp=BASE_TIME + timedelta(seconds=52),
    )

    assert recovered.alarm is not None
    assert recovered.receipt is not None

    assert recovered.receipt.disposition is (
        AlarmDisposition.RESOLVED
    )

    assert recovered.alarm.state is AlarmState.RESOLVED
    assert recovered.alarm.alarm_id == raised_alarm_id

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()
