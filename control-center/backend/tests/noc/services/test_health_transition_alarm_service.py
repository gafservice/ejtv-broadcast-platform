"""Tests for NodeHealth transition operational alarm coordination."""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_alarm import (
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_service import (
    AlarmDisposition,
    AlarmService,
)
from app.noc.services.health_transition_alarm_service import (
    HealthTransitionAlarmResult,
    HealthTransitionAlarmService,
)


BASE_TIME = datetime(
    2026,
    8,
    21,
    22,
    45,
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
        return self.nodes.pop(node_id.id, None) is not None

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

    service = HealthTransitionAlarmService(
        alarm_service=alarm_service,
    )

    return (
        node,
        instance,
        alarm_service,
        service,
    )


def health(
    state: NodeHealthState,
) -> NodeHealth:
    return NodeHealth(state)


def test_service_requires_alarm_service() -> None:
    with pytest.raises(TypeError):
        HealthTransitionAlarmService(
            alarm_service=object(),  # type: ignore[arg-type]
        )


def test_first_observation_does_not_raise_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=None,
        current=health(NodeHealthState.HEALTHY),
        timestamp=BASE_TIME,
    )

    assert isinstance(
        result,
        HealthTransitionAlarmResult,
    )
    assert result.transition is None
    assert result.alarm is None
    assert result.receipt is None
    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_same_health_does_not_raise_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.HEALTHY),
        timestamp=BASE_TIME,
    )

    assert result.transition is None
    assert result.alarm is None
    assert result.receipt is None
    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


@pytest.mark.parametrize(
    ("state", "severity"),
    (
        (
            NodeHealthState.WARNING,
            AlarmSeverity.WARNING,
        ),
        (
            NodeHealthState.DEGRADED,
            AlarmSeverity.MAJOR,
        ),
        (
            NodeHealthState.CRITICAL,
            AlarmSeverity.CRITICAL,
        ),
    ),
)
def test_degradation_raises_operational_alarm(
    state: NodeHealthState,
    severity: AlarmSeverity,
) -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(state),
        timestamp=BASE_TIME,
    )

    assert result.transition is not None
    assert result.alarm is not None
    assert result.receipt is not None

    assert result.receipt.disposition is (
        AlarmDisposition.RAISED
    )
    assert result.alarm.state is AlarmState.ACTIVE
    assert result.alarm.severity is severity
    assert result.alarm.alarm_type == (
        "NODE_HEALTH_DEGRADED"
    )

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert active == (result.alarm,)


def test_existing_health_alarm_prevents_duplicate() -> None:
    node, instance, alarm_service, service = make_context()

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.WARNING),
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.WARNING),
        current=health(NodeHealthState.CRITICAL),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert first.alarm is not None
    assert first.receipt is not None

    assert second.transition is not None
    assert second.alarm is first.alarm
    assert second.receipt is None

    active = alarm_service.active(
        node.node_id,
        instance.instance_id,
    )

    assert active == (first.alarm,)


def test_recovery_resolves_active_health_alarm() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.CRITICAL),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.CRITICAL),
        current=health(NodeHealthState.HEALTHY),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert recovered.transition is not None
    assert recovered.alarm is not None
    assert recovered.receipt is not None

    assert recovered.receipt.disposition is (
        AlarmDisposition.RESOLVED
    )
    assert recovered.alarm.state is AlarmState.RESOLVED
    assert recovered.alarm.alarm_id == (
        raised.alarm.alarm_id
    )

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_recovery_without_active_alarm_is_noop() -> None:
    node, instance, alarm_service, service = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.CRITICAL),
        current=health(NodeHealthState.HEALTHY),
        timestamp=BASE_TIME,
    )

    assert result.transition is not None
    assert result.alarm is None
    assert result.receipt is None
    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_acknowledged_alarm_is_resolved_on_recovery() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.CRITICAL),
        timestamp=BASE_TIME,
    )

    assert raised.alarm is not None

    acknowledged = alarm_service.acknowledge(
        node.node_id,
        instance.instance_id,
        raised.alarm.alarm_id,
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert acknowledged.alarm.state is (
        AlarmState.ACKNOWLEDGED
    )

    recovered = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.CRITICAL),
        current=health(NodeHealthState.HEALTHY),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert recovered.alarm is not None
    assert recovered.alarm.state is AlarmState.RESOLVED
    assert recovered.alarm.acknowledged is True
    assert recovered.alarm.acknowledged_by == "operator"


def test_improvement_without_recovery_keeps_alarm_active() -> None:
    node, instance, alarm_service, service = make_context()

    raised = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.CRITICAL),
        timestamp=BASE_TIME,
    )

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.CRITICAL),
        current=health(NodeHealthState.DEGRADED),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert raised.alarm is not None
    assert result.transition is not None
    assert result.alarm is raised.alarm
    assert result.receipt is None

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == (raised.alarm,)


def test_process_requires_node_id() -> None:
    _, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=object(),  # type: ignore[arg-type]
            instance_id=instance.instance_id,
            previous=health(NodeHealthState.HEALTHY),
            current=health(NodeHealthState.WARNING),
            timestamp=BASE_TIME,
        )


def test_process_requires_instance_id() -> None:
    node, _, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id="streaming-primary",  # type: ignore[arg-type]
            previous=health(NodeHealthState.HEALTHY),
            current=health(NodeHealthState.WARNING),
            timestamp=BASE_TIME,
        )


def test_process_requires_current_health() -> None:
    node, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            previous=health(NodeHealthState.HEALTHY),
            current=object(),  # type: ignore[arg-type]
            timestamp=BASE_TIME,
        )


def test_process_requires_timestamp() -> None:
    node, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            previous=health(NodeHealthState.HEALTHY),
            current=health(NodeHealthState.WARNING),
            timestamp="2026-08-21",  # type: ignore[arg-type]
        )
