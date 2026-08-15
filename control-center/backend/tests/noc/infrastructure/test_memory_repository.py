"""Tests for InMemoryNodeRepository."""

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.registry.repository import NodeRepository


def make_node(
    node_id: str = "streaming-core",
    *,
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


def test_repository_satisfies_protocol() -> None:
    repository = InMemoryNodeRepository()

    assert isinstance(
        repository,
        NodeRepository,
    )


def test_repository_starts_empty() -> None:
    repository = InMemoryNodeRepository()

    assert repository.count() == 0
    assert repository.list_all() == ()


def test_save_and_get_node() -> None:
    repository = InMemoryNodeRepository()
    node = make_node()

    repository.save(node)

    assert repository.get(
        node.node_id
    ) is node

    assert repository.count() == 1


def test_exists_false_before_save() -> None:
    repository = InMemoryNodeRepository()
    node = make_node()

    assert repository.exists(
        node.node_id
    ) is False


def test_exists_true_after_save() -> None:
    repository = InMemoryNodeRepository()
    node = make_node()

    repository.save(node)

    assert repository.exists(
        node.node_id
    ) is True


def test_get_unknown_returns_none() -> None:
    repository = InMemoryNodeRepository()

    unknown = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    assert repository.get(
        unknown
    ) is None


def test_save_replaces_same_identity() -> None:
    repository = InMemoryNodeRepository()

    original = make_node(
        "streaming-core"
    )

    replacement = Node(
        node_id=original.node_id,
        node_type=NodeType.STREAMING,
    )

    repository.save(original)
    repository.save(replacement)

    assert repository.count() == 1

    assert repository.get(
        original.node_id
    ) is replacement


def test_multiple_nodes_are_stored() -> None:
    repository = InMemoryNodeRepository()

    first = make_node(
        "streaming-core"
    )

    second = make_node(
        "transcoding-core"
    )

    repository.save(first)
    repository.save(second)

    assert repository.count() == 2


def test_list_all_is_deterministic() -> None:
    repository = InMemoryNodeRepository()

    repository.save(
        make_node("node-c")
    )

    repository.save(
        make_node("node-a")
    )

    repository.save(
        make_node("node-b")
    )

    assert [
        node.node_id.id
        for node in repository.list_all()
    ] == [
        "node-a",
        "node-b",
        "node-c",
    ]


def test_delete_existing_node() -> None:
    repository = InMemoryNodeRepository()
    node = make_node()

    repository.save(node)

    removed = repository.delete(
        node.node_id
    )

    assert removed is True

    assert repository.exists(
        node.node_id
    ) is False

    assert repository.count() == 0


def test_delete_unknown_returns_false() -> None:
    repository = InMemoryNodeRepository()

    unknown = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    assert repository.delete(
        unknown
    ) is False


def test_clear_removes_all_nodes() -> None:
    repository = InMemoryNodeRepository()

    repository.save(
        make_node("node-a")
    )

    repository.save(
        make_node("node-b")
    )

    repository.clear()

    assert repository.count() == 0
    assert repository.list_all() == ()


def test_save_rejects_non_node() -> None:
    repository = InMemoryNodeRepository()

    with pytest.raises(TypeError):
        repository.save(
            "node"  # type: ignore[arg-type]
        )


def test_get_rejects_non_node_id() -> None:
    repository = InMemoryNodeRepository()

    with pytest.raises(TypeError):
        repository.get(
            "streaming-core"  # type: ignore[arg-type]
        )


def test_exists_rejects_non_node_id() -> None:
    repository = InMemoryNodeRepository()

    with pytest.raises(TypeError):
        repository.exists(
            "streaming-core"  # type: ignore[arg-type]
        )


def test_delete_rejects_non_node_id() -> None:
    repository = InMemoryNodeRepository()

    with pytest.raises(TypeError):
        repository.delete(
            "streaming-core"  # type: ignore[arg-type]
        )


def test_node_instances_survive_repository_round_trip() -> None:
    repository = InMemoryNodeRepository()
    node = make_node()

    node.create_instance(
        instance_id="streaming-primary"
    )

    node.create_instance(
        instance_id="streaming-backup"
    )

    repository.save(node)

    stored = repository.get(
        node.node_id
    )

    assert stored is not None
    assert stored.instance_count == 2


def test_repository_integrates_with_node_registry() -> None:
    from app.noc.registry.registry import NodeRegistry

    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = make_node()

    registry.register(node)

    assert registry.require(
        node.node_id
    ) is node

    assert registry.count() == 1
