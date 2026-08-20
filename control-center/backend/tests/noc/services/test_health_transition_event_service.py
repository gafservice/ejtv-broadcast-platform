from datetime import datetime, timezone

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_event import EventSeverity
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import NodeRegistry
from app.noc.services.event_service import EventService
from app.noc.services.health_transition_event_service import (
    HealthTransitionEventResult,
    HealthTransitionEventService,
)


BASE_TIME = datetime(
    2026,
    8,
    20,
    21,
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

    event_service = EventService(registry)

    service = HealthTransitionEventService(
        event_service=event_service,
    )

    return (
        repository,
        registry,
        node,
        instance,
        event_service,
        service,
    )


def health(
    state: NodeHealthState,
) -> NodeHealth:
    return NodeHealth(state)


def test_service_requires_event_service():
    with pytest.raises(TypeError):
        HealthTransitionEventService(
            event_service=object(),  # type: ignore[arg-type]
        )


def test_first_observation_does_not_generate_event():
    (
        _,
        _,
        node,
        instance,
        event_service,
        service,
    ) = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=None,
        current=health(NodeHealthState.HEALTHY),
        timestamp=BASE_TIME,
    )

    assert isinstance(
        result,
        HealthTransitionEventResult,
    )
    assert result.transition is None
    assert result.event is None
    assert result.receipt is None

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_same_health_does_not_generate_event():
    (
        _,
        _,
        node,
        instance,
        event_service,
        service,
    ) = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.HEALTHY),
        timestamp=BASE_TIME,
    )

    assert result.transition is None
    assert result.event is None
    assert result.receipt is None

    assert event_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_healthy_to_warning_records_event():
    (
        _,
        _,
        node,
        instance,
        event_service,
        service,
    ) = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.WARNING),
        timestamp=BASE_TIME,
    )

    assert result.transition is not None
    assert result.event is not None
    assert result.receipt is not None

    assert result.event.event_type == (
        "NODE_HEALTH_DEGRADED"
    )
    assert result.event.severity is (
        EventSeverity.WARNING
    )

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert len(events) == 1
    assert events[0] is result.event


def test_healthy_to_critical_records_critical_event():
    (
        _,
        _,
        node,
        instance,
        event_service,
        service,
    ) = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.CRITICAL),
        timestamp=BASE_TIME,
    )

    assert result.transition is not None
    assert result.event is not None
    assert result.receipt is not None

    assert result.event.event_type == (
        "NODE_HEALTH_DEGRADED"
    )
    assert result.event.severity is (
        EventSeverity.CRITICAL
    )

    assert result.event.attributes is not None
    assert result.event.attributes["previous"] == (
        "HEALTHY"
    )
    assert result.event.attributes["current"] == (
        "CRITICAL"
    )


def test_critical_to_healthy_records_recovery_event():
    (
        _,
        _,
        node,
        instance,
        event_service,
        service,
    ) = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.CRITICAL),
        current=health(NodeHealthState.HEALTHY),
        timestamp=BASE_TIME,
    )

    assert result.transition is not None
    assert result.event is not None
    assert result.receipt is not None

    assert result.event.event_type == (
        "NODE_HEALTH_RECOVERED"
    )
    assert result.event.severity is (
        EventSeverity.INFO
    )

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert len(events) == 1
    assert events[0].event_type == (
        "NODE_HEALTH_RECOVERED"
    )


def test_critical_to_degraded_records_improvement_event():
    (
        _,
        _,
        node,
        instance,
        event_service,
        service,
    ) = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.CRITICAL),
        current=health(NodeHealthState.DEGRADED),
        timestamp=BASE_TIME,
    )

    assert result.event is not None

    assert result.event.event_type == (
        "NODE_HEALTH_IMPROVED"
    )
    assert result.event.severity is (
        EventSeverity.NOTICE
    )


def test_transition_to_unknown_records_unknown_event():
    (
        _,
        _,
        node,
        instance,
        event_service,
        service,
    ) = make_context()

    result = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.UNKNOWN),
        timestamp=BASE_TIME,
    )

    assert result.event is not None

    assert result.event.event_type == (
        "NODE_HEALTH_UNKNOWN"
    )
    assert result.event.severity is (
        EventSeverity.NOTICE
    )


def test_multiple_transitions_append_multiple_events():
    (
        _,
        _,
        node,
        instance,
        event_service,
        service,
    ) = make_context()

    first = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.HEALTHY),
        current=health(NodeHealthState.CRITICAL),
        timestamp=BASE_TIME,
    )

    second = service.process(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        previous=health(NodeHealthState.CRITICAL),
        current=health(NodeHealthState.HEALTHY),
        timestamp=BASE_TIME,
    )

    assert first.event is not None
    assert second.event is not None

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert len(events) == 2

    assert events[0].event_type == (
        "NODE_HEALTH_DEGRADED"
    )
    assert events[1].event_type == (
        "NODE_HEALTH_RECOVERED"
    )


def test_process_requires_node_id():
    *_, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=object(),  # type: ignore[arg-type]
            instance_id=instance.instance_id,
            previous=health(NodeHealthState.HEALTHY),
            current=health(NodeHealthState.WARNING),
            timestamp=BASE_TIME,
        )


def test_process_requires_instance_id():
    *_, node, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id="streaming-primary",  # type: ignore[arg-type]
            previous=health(NodeHealthState.HEALTHY),
            current=health(NodeHealthState.WARNING),
            timestamp=BASE_TIME,
        )


def test_process_requires_current_health():
    (
        _,
        _,
        node,
        instance,
        _,
        service,
    ) = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            previous=health(NodeHealthState.HEALTHY),
            current=object(),  # type: ignore[arg-type]
            timestamp=BASE_TIME,
        )


def test_process_requires_timestamp():
    (
        _,
        _,
        node,
        instance,
        _,
        service,
    ) = make_context()

    with pytest.raises(TypeError):
        service.process(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            previous=health(NodeHealthState.HEALTHY),
            current=health(NodeHealthState.WARNING),
            timestamp="2026-08-20",  # type: ignore[arg-type]
        )

