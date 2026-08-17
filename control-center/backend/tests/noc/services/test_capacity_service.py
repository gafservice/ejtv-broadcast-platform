"""Tests for CapacityService.

ENG-013B — Node SDK
NCS reference: 15-NODE-CAPACITY.md
"""

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_capacity import (
    CapacityResource,
    NodeCapacity,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import (
    NodeNotFoundError,
    NodeRegistry,
)
from app.noc.services.capacity_service import (
    CapacityService,
    NodeInstanceNotFoundError,
)


class MemoryRepository:
    def __init__(self) -> None:
        self.nodes = {}

    def save(self, node):
        self.nodes[node.node_id.id] = node

    def get(self, node_id):
        return self.nodes.get(
            node_id.id
        )

    def exists(self, node_id):
        return node_id.id in self.nodes

    def list_all(self):
        return tuple(
            self.nodes.values()
        )

    def delete(self, node_id):
        return (
            self.nodes.pop(
                node_id.id,
                None,
            )
            is not None
        )

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

    return (
        repository,
        registry,
        node,
        instance,
        CapacityService(registry),
    )


def make_capacity(
    *,
    memory_maximum: int = 8_000_000_000,
    memory_allocated: int = 3_000_000_000,
    memory_available: int = 5_000_000_000,
) -> NodeCapacity:
    return NodeCapacity(
        resources=(
            CapacityResource(
                resource="System Memory",
                maximum=memory_maximum,
                allocated=memory_allocated,
                reserved=0,
                available=memory_available,
                unit="bytes",
            ),
        )
    )


def test_service_requires_registry() -> None:
    with pytest.raises(TypeError):
        CapacityService(
            object()  # type: ignore[arg-type]
        )


def test_current_returns_none_before_publication() -> None:
    _, _, node, instance, service = make_context()

    result = service.current(
        node.node_id,
        instance.instance_id,
    )

    assert result is None


def test_publish_stores_capacity_on_instance() -> None:
    _, _, node, instance, service = make_context()

    capacity = make_capacity()

    result = service.publish(
        node.node_id,
        instance.instance_id,
        capacity,
    )

    assert result is capacity
    assert instance.capacity is capacity


def test_publish_persists_changed_node() -> None:
    repository, _, node, instance, service = make_context()

    capacity = make_capacity()

    service.publish(
        node.node_id,
        instance.instance_id,
        capacity,
    )

    persisted = repository.get(
        node.node_id
    )

    assert persisted is node
    assert persisted.instances[0].capacity is capacity


def test_current_returns_published_capacity() -> None:
    _, _, node, instance, service = make_context()

    capacity = make_capacity()

    service.publish(
        node.node_id,
        instance.instance_id,
        capacity,
    )

    assert service.current(
        node.node_id,
        instance.instance_id,
    ) is capacity


def test_publish_replaces_previous_capacity() -> None:
    _, _, node, instance, service = make_context()

    first = make_capacity()

    second = make_capacity(
        memory_allocated=4_000_000_000,
        memory_available=4_000_000_000,
    )

    service.publish(
        node.node_id,
        instance.instance_id,
        first,
    )

    service.publish(
        node.node_id,
        instance.instance_id,
        second,
    )

    assert service.current(
        node.node_id,
        instance.instance_id,
    ) is second

    assert instance.capacity is second


def test_publish_requires_node_id() -> None:
    _, _, _, instance, service = make_context()

    with pytest.raises(TypeError):
        service.publish(
            object(),  # type: ignore[arg-type]
            instance.instance_id,
            make_capacity(),
        )


def test_publish_requires_instance_id() -> None:
    _, _, node, _, service = make_context()

    with pytest.raises(TypeError):
        service.publish(
            node.node_id,
            object(),  # type: ignore[arg-type]
            make_capacity(),
        )


def test_publish_requires_capacity() -> None:
    _, _, node, instance, service = make_context()

    with pytest.raises(TypeError):
        service.publish(
            node.node_id,
            instance.instance_id,
            object(),  # type: ignore[arg-type]
        )


def test_publish_rejects_unknown_node() -> None:
    _, _, _, instance, service = make_context()

    unknown_node_id = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown Node",
    )

    with pytest.raises(NodeNotFoundError):
        service.publish(
            unknown_node_id,
            instance.instance_id,
            make_capacity(),
        )


def test_publish_rejects_unknown_instance() -> None:
    _, _, node, _, service = make_context()

    with pytest.raises(NodeInstanceNotFoundError):
        service.publish(
            node.node_id,
            NodeInstanceId("missing-instance"),
            make_capacity(),
        )


def test_current_rejects_unknown_instance() -> None:
    _, _, node, _, service = make_context()

    with pytest.raises(NodeInstanceNotFoundError):
        service.current(
            node.node_id,
            NodeInstanceId("missing-instance"),
        )


def test_current_requires_node_id() -> None:
    _, _, _, instance, service = make_context()

    with pytest.raises(TypeError):
        service.current(
            object(),  # type: ignore[arg-type]
            instance.instance_id,
        )


def test_current_requires_instance_id() -> None:
    _, _, node, _, service = make_context()

    with pytest.raises(TypeError):
        service.current(
            node.node_id,
            object(),  # type: ignore[arg-type]
        )
