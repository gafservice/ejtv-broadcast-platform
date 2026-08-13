from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import (
    NodeNotFoundError,
    NodeRegistry,
)
from app.noc.services.alarm_service import (
    AlarmDisposition,
    AlarmNotFoundError,
    AlarmService,
    AlarmSourceMismatchError,
    DuplicateAlarmError,
    InvalidAlarmTransitionError,
    NodeInstanceNotFoundError,
)
from app.noc.services.snapshot_service import SnapshotService


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
        return self.nodes.pop(node_id.id, None) is not None

    def count(self):
        return len(self.nodes)


BASE_TIME = datetime(
    2026,
    8,
    13,
    22,
    0,
    tzinfo=timezone.utc,
)


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

    return (
        repository,
        registry,
        node,
        instance,
        AlarmService(registry),
    )


def make_alarm(
    *,
    alarm_id="alarm-001",
    state=AlarmState.ACTIVE,
    source="streaming-primary",
    severity=AlarmSeverity.MAJOR,
):
    return AlarmRecord(
        alarm_id=alarm_id,
        alarm_type="CPU_HIGH",
        severity=severity,
        state=state,
        timestamp=BASE_TIME,
        source=NodeInstanceId(source),
        title="CPU usage high",
        description="CPU exceeded threshold",
    )


def test_service_requires_registry():
    with pytest.raises(TypeError):
        AlarmService(
            object()  # type: ignore[arg-type]
        )


def test_raise_alarm():
    _, _, node, instance, service = make_context()

    alarm = make_alarm()

    receipt = service.raise_alarm(
        node.node_id,
        instance.instance_id,
        alarm,
    )

    assert receipt.disposition is AlarmDisposition.RAISED
    assert receipt.alarm is alarm
    assert instance.alarms == (alarm,)


def test_raise_alarm_rejects_duplicate_id():
    _, _, node, instance, service = make_context()

    alarm = make_alarm()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        alarm,
    )

    with pytest.raises(DuplicateAlarmError):
        service.raise_alarm(
            node.node_id,
            instance.instance_id,
            make_alarm(),
        )


def test_raise_alarm_rejects_wrong_source():
    _, _, node, instance, service = make_context()

    with pytest.raises(AlarmSourceMismatchError):
        service.raise_alarm(
            node.node_id,
            instance.instance_id,
            make_alarm(
                source="streaming-backup"
            ),
        )


def test_new_alarm_must_be_active():
    _, _, node, instance, service = make_context()

    resolved = AlarmRecord(
        alarm_id="alarm-001",
        alarm_type="CPU_HIGH",
        severity=AlarmSeverity.MAJOR,
        state=AlarmState.RESOLVED,
        timestamp=BASE_TIME,
        source=instance.instance_id,
        title="CPU usage high",
        description="CPU exceeded threshold",
        resolved_at=BASE_TIME + timedelta(seconds=5),
    )

    with pytest.raises(InvalidAlarmTransitionError):
        service.raise_alarm(
            node.node_id,
            instance.instance_id,
            resolved,
        )


def test_acknowledge_active_alarm():
    _, _, node, instance, service = make_context()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        make_alarm(),
    )

    receipt = service.acknowledge(
        node.node_id,
        instance.instance_id,
        "alarm-001",
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert receipt.disposition is AlarmDisposition.ACKNOWLEDGED
    assert receipt.alarm.state is AlarmState.ACKNOWLEDGED
    assert receipt.alarm.acknowledged is True
    assert receipt.alarm.acknowledged_by == "operator"
    assert receipt.alarm.acknowledged_at == (
        BASE_TIME + timedelta(seconds=5)
    )


def test_acknowledged_alarm_replaces_previous_record():
    _, _, node, instance, service = make_context()

    original = make_alarm()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        original,
    )

    receipt = service.acknowledge(
        node.node_id,
        instance.instance_id,
        original.alarm_id,
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert instance.alarms[0] is receipt.alarm
    assert instance.alarms[0] is not original


def test_cannot_acknowledge_twice():
    _, _, node, instance, service = make_context()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        make_alarm(),
    )

    service.acknowledge(
        node.node_id,
        instance.instance_id,
        "alarm-001",
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    with pytest.raises(InvalidAlarmTransitionError):
        service.acknowledge(
            node.node_id,
            instance.instance_id,
            "alarm-001",
            acknowledged_by="operator",
            timestamp=BASE_TIME + timedelta(seconds=6),
        )


def test_resolve_active_alarm():
    _, _, node, instance, service = make_context()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        make_alarm(),
    )

    receipt = service.resolve(
        node.node_id,
        instance.instance_id,
        "alarm-001",
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert receipt.disposition is AlarmDisposition.RESOLVED
    assert receipt.alarm.state is AlarmState.RESOLVED
    assert receipt.alarm.resolved_at == (
        BASE_TIME + timedelta(seconds=10)
    )


def test_resolve_acknowledged_alarm_preserves_ack():
    _, _, node, instance, service = make_context()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        make_alarm(),
    )

    service.acknowledge(
        node.node_id,
        instance.instance_id,
        "alarm-001",
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    receipt = service.resolve(
        node.node_id,
        instance.instance_id,
        "alarm-001",
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert receipt.alarm.state is AlarmState.RESOLVED
    assert receipt.alarm.acknowledged is True
    assert receipt.alarm.acknowledged_by == "operator"


def test_close_resolved_alarm():
    _, _, node, instance, service = make_context()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        make_alarm(),
    )

    service.resolve(
        node.node_id,
        instance.instance_id,
        "alarm-001",
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    receipt = service.close(
        node.node_id,
        instance.instance_id,
        "alarm-001",
        timestamp=BASE_TIME + timedelta(seconds=20),
    )

    assert receipt.disposition is AlarmDisposition.CLOSED
    assert receipt.alarm.state is AlarmState.CLOSED
    assert receipt.alarm.closed_at == (
        BASE_TIME + timedelta(seconds=20)
    )


def test_cannot_close_active_alarm():
    _, _, node, instance, service = make_context()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        make_alarm(),
    )

    with pytest.raises(InvalidAlarmTransitionError):
        service.close(
            node.node_id,
            instance.instance_id,
            "alarm-001",
            timestamp=BASE_TIME + timedelta(seconds=10),
        )


def test_get_alarm():
    _, _, node, instance, service = make_context()

    alarm = make_alarm()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        alarm,
    )

    assert service.get(
        node.node_id,
        instance.instance_id,
        alarm.alarm_id,
    ) is alarm


def test_get_unknown_alarm_returns_none():
    _, _, node, instance, service = make_context()

    assert service.get(
        node.node_id,
        instance.instance_id,
        "missing",
    ) is None


def test_transition_unknown_alarm_raises():
    _, _, node, instance, service = make_context()

    with pytest.raises(AlarmNotFoundError):
        service.resolve(
            node.node_id,
            instance.instance_id,
            "missing",
            timestamp=BASE_TIME,
        )


def test_list_all():
    _, _, node, instance, service = make_context()

    first = make_alarm(
        alarm_id="alarm-001"
    )

    second = make_alarm(
        alarm_id="alarm-002",
        severity=AlarmSeverity.WARNING,
    )

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        first,
    )

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        second,
    )

    assert service.list_all(
        node.node_id,
        instance.instance_id,
    ) == (
        first,
        second,
    )


def test_active_returns_only_attention_alarms():
    _, _, node, instance, service = make_context()

    first = make_alarm(
        alarm_id="alarm-001"
    )

    second = make_alarm(
        alarm_id="alarm-002"
    )

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        first,
    )

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        second,
    )

    service.resolve(
        node.node_id,
        instance.instance_id,
        "alarm-002",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    active = service.active(
        node.node_id,
        instance.instance_id,
    )

    assert active == (first,)


def test_snapshot_contains_active_alarm():
    _, registry, node, instance, service = make_context()

    alarm = make_alarm()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        alarm,
    )

    snapshot = SnapshotService(
        registry
    ).build(
        node.node_id,
        instance.instance_id,
        timestamp=BASE_TIME,
    )

    assert snapshot.alarms is not None
    assert snapshot.alarms.get(
        alarm.alarm_id
    ) == alarm


def test_snapshot_excludes_resolved_alarm():
    _, registry, node, instance, service = make_context()

    service.raise_alarm(
        node.node_id,
        instance.instance_id,
        make_alarm(),
    )

    service.resolve(
        node.node_id,
        instance.instance_id,
        "alarm-001",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    snapshot = SnapshotService(
        registry
    ).build(
        node.node_id,
        instance.instance_id,
        timestamp=BASE_TIME + timedelta(seconds=6),
    )

    assert snapshot.alarms is None


def test_unknown_node_is_rejected():
    _, _, _, instance, service = make_context()

    unknown = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    with pytest.raises(NodeNotFoundError):
        service.raise_alarm(
            unknown,
            instance.instance_id,
            make_alarm(),
        )


def test_unknown_instance_is_rejected():
    _, _, node, _, service = make_context()

    with pytest.raises(NodeInstanceNotFoundError):
        service.raise_alarm(
            node.node_id,
            NodeInstanceId("streaming-backup"),
            make_alarm(
                source="streaming-backup"
            ),
        )
