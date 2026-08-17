"""Tests for HealthService.

ENG-013B — Node SDK
NCS reference: 12-NODE-HEALTH.md
"""

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import (
    NodeNotFoundError,
    NodeRegistry,
)
from app.noc.services.health_service import (
    HealthService,
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
        HealthService(registry),
    )


def test_service_requires_registry() -> None:
    with pytest.raises(TypeError):
        HealthService(
            object()  # type: ignore[arg-type]
        )


def test_current_returns_none_before_publication() -> None:
    _, _, node, instance, service = make_context()

    result = service.current(
        node.node_id,
        instance.instance_id,
    )

    assert result is None


def test_publish_stores_health_on_instance() -> None:
    _, _, node, instance, service = make_context()

    health = NodeHealth(
        NodeHealthState.HEALTHY
    )

    result = service.publish(
        node.node_id,
        instance.instance_id,
        health,
    )

    assert result is health
    assert instance.health is health


def test_publish_persists_changed_node() -> None:
    repository, _, node, instance, service = make_context()

    health = NodeHealth(
        NodeHealthState.WARNING
    )

    service.publish(
        node.node_id,
        instance.instance_id,
        health,
    )

    persisted = repository.get(
        node.node_id
    )

    assert persisted is node
    assert persisted.instances[0].health is health


def test_current_returns_published_health() -> None:
    _, _, node, instance, service = make_context()

    health = NodeHealth(
        NodeHealthState.HEALTHY
    )

    service.publish(
        node.node_id,
        instance.instance_id,
        health,
    )

    assert service.current(
        node.node_id,
        instance.instance_id,
    ) is health


def test_publish_replaces_previous_health() -> None:
    _, _, node, instance, service = make_context()

    first = NodeHealth(
        NodeHealthState.HEALTHY
    )

    second = NodeHealth(
        NodeHealthState.WARNING
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

    assert instance.health is second


def test_publish_requires_node_id() -> None:
    _, _, _, instance, service = make_context()

    with pytest.raises(TypeError):
        service.publish(
            object(),  # type: ignore[arg-type]
            instance.instance_id,
            NodeHealth(NodeHealthState.HEALTHY),
        )


def test_publish_requires_instance_id() -> None:
    _, _, node, _, service = make_context()

    with pytest.raises(TypeError):
        service.publish(
            node.node_id,
            object(),  # type: ignore[arg-type]
            NodeHealth(NodeHealthState.HEALTHY),
        )


def test_publish_requires_health() -> None:
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
            NodeHealth(NodeHealthState.HEALTHY),
        )


def test_publish_rejects_unknown_instance() -> None:
    _, _, node, _, service = make_context()

    with pytest.raises(NodeInstanceNotFoundError):
        service.publish(
            node.node_id,
            NodeInstanceId("missing-instance"),
            NodeHealth(NodeHealthState.HEALTHY),
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
