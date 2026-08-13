"""Tests for NodeRegistry.

ENG-013B — Node SDK
"""

from __future__ import annotations

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import (
    NodeAlreadyRegisteredError,
    NodeIdentityConflictError,
    NodeNotFoundError,
    NodeRegistry,
)
from app.noc.registry.repository import NodeRepository


class FakeNodeRepository:
    """In-memory test double for NodeRepository."""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}

    def save(
        self,
        node: Node,
    ) -> None:
        self._nodes[
            node.node_id.id
        ] = node

    def get(
        self,
        node_id: NodeId,
    ) -> Node | None:
        return self._nodes.get(
            node_id.id
        )

    def exists(
        self,
        node_id: NodeId,
    ) -> bool:
        return node_id.id in self._nodes

    def list_all(
        self,
    ) -> tuple[Node, ...]:
        return tuple(
            self._nodes.values()
        )

    def delete(
        self,
        node_id: NodeId,
    ) -> bool:
        return (
            self._nodes.pop(
                node_id.id,
                None,
            )
            is not None
        )

    def count(
        self,
    ) -> int:
        return len(self._nodes)


def make_node(
    node_id: str = "streaming-core",
    node_type: NodeType = NodeType.STREAMING,
) -> Node:
    return Node(
        node_id=NodeId.create(
            id=node_id,
            name=node_id,
            display_name=node_id,
        ),
        node_type=node_type,
    )


def make_registry() -> NodeRegistry:
    return NodeRegistry(
        FakeNodeRepository()
    )


def test_registry_accepts_repository_protocol() -> None:
    repository = FakeNodeRepository()

    assert isinstance(
        repository,
        NodeRepository,
    )

    registry = NodeRegistry(repository)

    assert registry.repository is repository


def test_registry_rejects_invalid_repository() -> None:
    with pytest.raises(TypeError):
        NodeRegistry(
            object()  # type: ignore[arg-type]
        )


def test_register_node() -> None:
    registry = make_registry()
    node = make_node()

    result = registry.register(node)

    assert result is node
    assert registry.count() == 1
    assert registry.is_registered(
        node.node_id
    ) is True


def test_register_persists_node() -> None:
    registry = make_registry()
    node = make_node()

    registry.register(node)

    assert registry.get(
        node.node_id
    ) is node


def test_register_rejects_invalid_node() -> None:
    registry = make_registry()

    with pytest.raises(TypeError):
        registry.register(
            "streaming-core"  # type: ignore[arg-type]
        )


def test_duplicate_registration_is_rejected() -> None:
    registry = make_registry()
    node = make_node()

    registry.register(node)

    duplicate = Node(
        node_id=node.node_id,
        node_type=NodeType.STREAMING,
    )

    with pytest.raises(
        NodeAlreadyRegisteredError
    ):
        registry.register(
            duplicate
        )

    assert registry.count() == 1


def test_node_type_identity_conflict_is_rejected() -> None:
    registry = make_registry()

    original = make_node(
        "core-node",
        NodeType.STREAMING,
    )

    registry.register(original)

    conflicting = Node(
        node_id=original.node_id,
        node_type=NodeType.STORAGE,
    )

    with pytest.raises(
        NodeIdentityConflictError
    ):
        registry.register(
            conflicting
        )

    stored = registry.require(
        original.node_id
    )

    assert stored.node_type is (
        NodeType.STREAMING
    )


def test_get_unknown_returns_none() -> None:
    registry = make_registry()

    node_id = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    assert registry.get(
        node_id
    ) is None


def test_require_returns_registered_node() -> None:
    registry = make_registry()
    node = make_node()

    registry.register(node)

    assert registry.require(
        node.node_id
    ) is node


def test_require_unknown_raises() -> None:
    registry = make_registry()

    node_id = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    with pytest.raises(
        NodeNotFoundError
    ):
        registry.require(
            node_id
        )


def test_is_registered_rejects_invalid_node_id() -> None:
    registry = make_registry()

    with pytest.raises(TypeError):
        registry.is_registered(
            "streaming-core"  # type: ignore[arg-type]
        )


def test_list_nodes_returns_tuple() -> None:
    registry = make_registry()

    registry.register(
        make_node("node-a")
    )

    result = registry.list_nodes()

    assert isinstance(
        result,
        tuple,
    )


def test_list_nodes_is_deterministic() -> None:
    registry = make_registry()

    registry.register(
        make_node("node-c")
    )

    registry.register(
        make_node("node-a")
    )

    registry.register(
        make_node("node-b")
    )

    result = registry.list_nodes()

    assert [
        node.node_id.id
        for node in result
    ] == [
        "node-a",
        "node-b",
        "node-c",
    ]


def test_registry_count() -> None:
    registry = make_registry()

    registry.register(
        make_node("node-a")
    )

    registry.register(
        make_node("node-b")
    )

    assert registry.count() == 2
    assert len(registry) == 2


def test_contains_registered_node_id() -> None:
    registry = make_registry()
    node = make_node()

    registry.register(node)

    assert node.node_id in registry


def test_contains_unknown_node_id() -> None:
    registry = make_registry()

    node_id = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    assert node_id not in registry


def test_contains_non_node_id_returns_false() -> None:
    registry = make_registry()

    assert (
        "streaming-core"
        not in registry
    )


def test_retire_node() -> None:
    registry = make_registry()
    node = make_node()

    registry.register(node)

    retired = registry.retire(
        node.node_id
    )

    assert retired is node
    assert registry.count() == 0
    assert registry.is_registered(
        node.node_id
    ) is False


def test_retire_unknown_node_raises() -> None:
    registry = make_registry()

    node_id = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    with pytest.raises(
        NodeNotFoundError
    ):
        registry.retire(
            node_id
        )


def test_node_without_instances_remains_registered() -> None:
    """Zero NodeInstances must not imply automatic Node removal."""
    registry = make_registry()
    node = make_node()

    assert node.instance_count == 0

    registry.register(node)

    assert registry.is_registered(
        node.node_id
    ) is True

    assert registry.count() == 1


def test_registry_keeps_node_instances_inside_aggregate() -> None:
    registry = make_registry()
    node = make_node()

    node.create_instance(
        instance_id="streaming-primary"
    )

    node.create_instance(
        instance_id="streaming-backup"
    )

    registry.register(node)

    stored = registry.require(
        node.node_id
    )

    assert stored.instance_count == 2

    assert {
        str(instance)
        for instance in stored.instances
    } == {
        "streaming-primary",
        "streaming-backup",
    }
