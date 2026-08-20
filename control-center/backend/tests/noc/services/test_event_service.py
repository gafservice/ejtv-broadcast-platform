from datetime import datetime, timezone

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import (
    NodeNotFoundError,
    NodeRegistry,
)
from app.noc.services.event_service import (
    DuplicateEventError,
    EventDisposition,
    EventService,
    EventSourceMismatchError,
    NodeInstanceNotFoundError,
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


BASE_TIME = datetime(
    2026,
    8,
    20,
    20,
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
        EventService(registry),
    )


def make_event(
    *,
    event_id="event-001",
    event_type="NODE_HEALTH_CHANGED",
    source="streaming-primary",
    severity=EventSeverity.CRITICAL,
):
    return EventRecord(
        event_id=event_id,
        event_type=event_type,
        severity=severity,
        timestamp=BASE_TIME,
        source=NodeInstanceId(source),
        title="Node health changed",
        description="Node health transitioned to CRITICAL",
    )


def test_service_requires_registry():
    with pytest.raises(TypeError):
        EventService(
            object()  # type: ignore[arg-type]
        )


def test_record_event():
    _, _, node, instance, service = make_context()

    event = make_event()

    receipt = service.record(
        node.node_id,
        instance.instance_id,
        event,
    )

    assert receipt.disposition is EventDisposition.RECORDED
    assert receipt.event is event
    assert instance.events == (event,)


def test_record_rejects_duplicate_id():
    _, _, node, instance, service = make_context()

    event = make_event()

    service.record(
        node.node_id,
        instance.instance_id,
        event,
    )

    with pytest.raises(DuplicateEventError):
        service.record(
            node.node_id,
            instance.instance_id,
            make_event(),
        )


def test_record_rejects_wrong_source():
    _, _, node, instance, service = make_context()

    with pytest.raises(EventSourceMismatchError):
        service.record(
            node.node_id,
            instance.instance_id,
            make_event(
                source="streaming-backup"
            ),
        )


def test_record_requires_event_record():
    _, _, node, instance, service = make_context()

    with pytest.raises(TypeError):
        service.record(
            node.node_id,
            instance.instance_id,
            object(),  # type: ignore[arg-type]
        )


def test_record_unknown_node():
    _, _, _, instance, service = make_context()

    unknown = NodeId.create(
        id="missing-node",
        name="missing",
        display_name="Missing Node",
    )

    with pytest.raises(NodeNotFoundError):
        service.record(
            unknown,
            instance.instance_id,
            make_event(),
        )


def test_record_unknown_instance():
    _, _, node, _, service = make_context()

    with pytest.raises(NodeInstanceNotFoundError):
        service.record(
            node.node_id,
            NodeInstanceId("missing-instance"),
            make_event(
                source="missing-instance"
            ),
        )


def test_current_returns_recorded_events():
    _, _, node, instance, service = make_context()

    first = make_event(
        event_id="event-001"
    )
    second = make_event(
        event_id="event-002",
        event_type="NODE_HEALTH_RECOVERED",
        severity=EventSeverity.INFO,
    )

    service.record(
        node.node_id,
        instance.instance_id,
        first,
    )
    service.record(
        node.node_id,
        instance.instance_id,
        second,
    )

    events = service.current(
        node.node_id,
        instance.instance_id,
    )

    assert events.events == (
        first,
        second,
    )


def test_get_returns_recorded_event():
    _, _, node, instance, service = make_context()

    event = make_event()

    service.record(
        node.node_id,
        instance.instance_id,
        event,
    )

    result = service.get(
        node.node_id,
        instance.instance_id,
        event.event_id,
    )

    assert result is event


def test_get_unknown_event_returns_none():
    _, _, node, instance, service = make_context()

    result = service.get(
        node.node_id,
        instance.instance_id,
        "missing-event",
    )

    assert result is None


def test_list_all_returns_recorded_events():
    _, _, node, instance, service = make_context()

    first = make_event(
        event_id="event-001"
    )
    second = make_event(
        event_id="event-002",
        event_type="NODE_HEALTH_RECOVERED",
        severity=EventSeverity.INFO,
    )

    service.record(
        node.node_id,
        instance.instance_id,
        first,
    )
    service.record(
        node.node_id,
        instance.instance_id,
        second,
    )

    result = service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert result == (
        first,
        second,
    )
