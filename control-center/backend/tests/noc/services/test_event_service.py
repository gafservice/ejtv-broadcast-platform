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
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.memory_repository import (
    InMemoryEventHistoryRepository,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)
from app.noc.history.sqlite_event_repository import (
    SQLiteEventHistoryRepository,
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


def test_service_accepts_optional_history_repository():
    repository = MemoryRepository()
    registry = NodeRegistry(repository)

    history = InMemoryEventHistoryRepository()

    service = EventService(
        registry,
        history_repository=history,
    )

    assert service.registry is registry
    assert service.history_repository is history


def test_service_rejects_invalid_history_repository():
    repository = MemoryRepository()
    registry = NodeRegistry(repository)

    with pytest.raises(TypeError):
        EventService(
            registry,
            history_repository=object(),
        )


def test_record_appends_event_to_history_repository():
    repository = MemoryRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
            created_at=BASE_TIME,
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    history = InMemoryEventHistoryRepository()

    service = EventService(
        registry,
        history_repository=history,
    )

    event = make_event()

    service.record(
        node.node_id,
        instance.instance_id,
        event,
    )

    historical = history.get(
        event.event_id
    )

    assert historical is not None
    assert historical.event == event
    assert historical.node_id == node.node_id
    assert historical.instance_id == (
        instance.instance_id
    )
    assert historical.recorded_at == (
        event.timestamp
    )


def test_record_persists_event_to_sqlite_history(
    tmp_path,
):
    database_path = (
        tmp_path / "noc-history.sqlite3"
    )

    repository = MemoryRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
            created_at=BASE_TIME,
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    database = SQLiteHistoryDatabase(
        database_path
    )

    history = SQLiteEventHistoryRepository(
        database
    )

    service = EventService(
        registry,
        history_repository=history,
    )

    event = make_event()

    service.record(
        node.node_id,
        instance.instance_id,
        event,
    )

    del service
    del history
    del database

    reopened = SQLiteEventHistoryRepository(
        SQLiteHistoryDatabase(
            database_path
        )
    )

    historical = reopened.get(
        event.event_id
    )

    assert historical is not None
    assert historical.event == event
    assert historical.node_id == node.node_id
    assert historical.instance_id == (
        instance.instance_id
    )


class FailingEventHistoryRepository(
    InMemoryEventHistoryRepository
):
    def append(self, record):
        raise RuntimeError(
            "simulated durable history failure"
        )


def test_history_failure_does_not_modify_instance_events():
    repository = MemoryRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
            created_at=BASE_TIME,
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    history = FailingEventHistoryRepository()

    service = EventService(
        registry,
        history_repository=history,
    )

    event = make_event()

    with pytest.raises(
        RuntimeError,
        match="simulated durable history failure",
    ):
        service.record(
            node.node_id,
            instance.instance_id,
            event,
        )

    assert instance.events == ()
    assert service.get(
        node.node_id,
        instance.instance_id,
        event.event_id,
    ) is None


class FailOnceNodeRepository(MemoryRepository):
    def __init__(self):
        super().__init__()
        self.fail_next_save = False

    def save(self, node):
        if self.fail_next_save:
            self.fail_next_save = False
            raise RuntimeError(
                "simulated node repository failure"
            )

        return super().save(node)


def test_record_retry_succeeds_when_durable_history_already_matches():
    repository = FailOnceNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
            created_at=BASE_TIME,
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    history = InMemoryEventHistoryRepository()

    service = EventService(
        registry,
        history_repository=history,
    )

    event = make_event()

    repository.fail_next_save = True

    with pytest.raises(
        RuntimeError,
        match="simulated node repository failure",
    ):
        service.record(
            node.node_id,
            instance.instance_id,
            event,
        )

    historical = history.get(
        event.event_id
    )

    assert historical is not None
    assert historical.event == event

    receipt = service.record(
        node.node_id,
        instance.instance_id,
        event,
    )

    assert receipt.disposition is EventDisposition.RECORDED
    assert receipt.event == event

    assert instance.events == (event,)

    historical = history.get(
        event.event_id
    )

    assert historical is not None
    assert historical.event == event


def test_record_rejects_conflicting_existing_durable_event():
    repository = MemoryRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
            created_at=BASE_TIME,
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    history = InMemoryEventHistoryRepository()

    original = make_event()

    history.append(
        EventHistoryRecord(
            event=original,
            node_id=node.node_id,
            instance_id=instance.instance_id,
            recorded_at=original.timestamp,
        )
    )

    conflicting = EventRecord(
        event_id=original.event_id,
        event_type=original.event_type,
        severity=original.severity,
        timestamp=original.timestamp,
        source=original.source,
        title="Conflicting event",
        description=original.description,
        attributes=original.attributes,
        correlation_id=original.correlation_id,
    )

    service = EventService(
        registry,
        history_repository=history,
    )

    with pytest.raises(
        DuplicateEventError,
        match="conflicting durable history",
    ):
        service.record(
            node.node_id,
            instance.instance_id,
            conflicting,
        )

    assert instance.events == ()

    historical = history.get(
        original.event_id
    )

    assert historical is not None
    assert historical.event == original
