"""Tests for reconnect flapping operational alarm coordination."""

from datetime import datetime, timezone

import pytest

from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
)
from app.noc.domain.logical_session_identity import (
    LogicalSessionIdentity,
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
from app.noc.services.reconnect_flapping_alarm_service import (
    ReconnectFlappingAlarmResult,
    ReconnectFlappingAlarmService,
)
from app.noc.services.reconnect_flapping_evaluator import (
    ReconnectFlappingEvaluation,
    ReconnectFlappingState,
)


BASE_TIME = datetime(
    2026,
    8,
    23,
    2,
    15,
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

    service = ReconnectFlappingAlarmService(
        alarm_service=alarm_service,
    )

    return (
        node,
        instance,
        alarm_service,
        service,
    )


def identity(
    *,
    remote_ip: str = "201.192.154.132",
    path: str = "ejtv",
) -> LogicalSessionIdentity:
    return LogicalSessionIdentity(
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        path=path,
        remote_ip=remote_ip,
    )


def evaluation(
    *,
    logical_identity: LogicalSessionIdentity | None = None,
    state: ReconnectFlappingState,
    reconnect_count: int = 3,
) -> ReconnectFlappingEvaluation:
    logical_identity = (
        logical_identity
        if logical_identity is not None
        else identity()
    )

    timestamps = tuple(
        BASE_TIME
        for _ in range(reconnect_count)
    )

    return ReconnectFlappingEvaluation(
        identity=logical_identity,
        state=state,
        observed_at=BASE_TIME,
        reconnect_count=reconnect_count,
        reconnect_timestamps=timestamps,
        reconnect_detected=(
            state is ReconnectFlappingState.FLAPPING
        ),
    )


def test_service_requires_alarm_service() -> None:
    with pytest.raises(TypeError):
        ReconnectFlappingAlarmService(
            alarm_service=object(),  # type: ignore[arg-type]
        )


def test_stable_without_alarm_is_noop() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            state=ReconnectFlappingState.STABLE,
            reconnect_count=0,
        ),
        timestamp=BASE_TIME,
    )

    assert isinstance(
        result,
        ReconnectFlappingAlarmResult,
    )
    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_flapping_raises_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            state=ReconnectFlappingState.FLAPPING,
        ),
        timestamp=BASE_TIME,
    )

    assert result.alarm is not None
    assert result.receipt is not None

    assert result.receipt.disposition is (
        AlarmDisposition.RAISED
    )
    assert result.alarm.state is AlarmState.ACTIVE
    assert result.alarm.alarm_type == "RECONNECT_FLAPPING"


def test_repeated_flapping_does_not_duplicate_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    flapping = evaluation(
        state=ReconnectFlappingState.FLAPPING,
    )

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=flapping,
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=flapping,
        timestamp=BASE_TIME,
    )

    assert first.alarm is not None
    assert second.alarm is first.alarm
    assert second.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == (first.alarm,)


def test_stable_resolves_active_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            state=ReconnectFlappingState.FLAPPING,
        ),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            state=ReconnectFlappingState.STABLE,
            reconnect_count=0,
        ),
        timestamp=BASE_TIME,
    )

    assert recovered.alarm is not None
    assert recovered.receipt is not None
    assert recovered.receipt.disposition is (
        AlarmDisposition.RESOLVED
    )
    assert recovered.alarm.state is AlarmState.RESOLVED
    assert recovered.alarm.alarm_id == (
        raised.alarm.alarm_id
    )


def test_acknowledged_alarm_resolves_when_stable() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            state=ReconnectFlappingState.FLAPPING,
        ),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    acknowledged = alarm_service.acknowledge(
        node.node_id,
        instance.instance_id,
        raised.alarm.alarm_id,
        acknowledged_by="operator",
        timestamp=BASE_TIME,
    )

    assert acknowledged.alarm.state is AlarmState.ACKNOWLEDGED

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            state=ReconnectFlappingState.STABLE,
            reconnect_count=0,
        ),
        timestamp=BASE_TIME,
    )

    assert recovered.alarm is not None
    assert recovered.alarm.state is AlarmState.RESOLVED
    assert recovered.alarm.acknowledged is True
    assert recovered.alarm.acknowledged_by == "operator"


def test_logical_identities_have_independent_alarms() -> None:
    node, instance, alarm_service, service = make_context()

    first_identity = identity(
        remote_ip="201.192.154.132",
    )

    second_identity = identity(
        remote_ip="190.10.20.30",
    )

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            logical_identity=first_identity,
            state=ReconnectFlappingState.FLAPPING,
        ),
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            logical_identity=second_identity,
            state=ReconnectFlappingState.FLAPPING,
        ),
        timestamp=BASE_TIME,
    )

    assert first.alarm is not None
    assert second.alarm is not None
    assert first.alarm.alarm_id != second.alarm.alarm_id

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert len(active) == 2


def test_recovery_resolves_only_matching_identity() -> None:
    node, instance, alarm_service, service = make_context()

    first_identity = identity(
        remote_ip="201.192.154.132",
    )

    second_identity = identity(
        remote_ip="190.10.20.30",
    )

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            logical_identity=first_identity,
            state=ReconnectFlappingState.FLAPPING,
        ),
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            logical_identity=second_identity,
            state=ReconnectFlappingState.FLAPPING,
        ),
        timestamp=BASE_TIME,
    )

    service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        evaluation=evaluation(
            logical_identity=first_identity,
            state=ReconnectFlappingState.STABLE,
            reconnect_count=0,
        ),
        timestamp=BASE_TIME,
    )

    assert first.alarm is not None
    assert second.alarm is not None

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert active == (second.alarm,)


def test_process_requires_node_id() -> None:
    _, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=object(),  # type: ignore[arg-type]
            instance_id=instance.instance_id,
            evaluation=evaluation(
                state=ReconnectFlappingState.STABLE,
                reconnect_count=0,
            ),
            timestamp=BASE_TIME,
        )


def test_process_requires_instance_id() -> None:
    node, _, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id="streaming-primary",  # type: ignore[arg-type]
            evaluation=evaluation(
                state=ReconnectFlappingState.STABLE,
                reconnect_count=0,
            ),
            timestamp=BASE_TIME,
        )


def test_process_requires_evaluation() -> None:
    node, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            evaluation=object(),  # type: ignore[arg-type]
            timestamp=BASE_TIME,
        )
