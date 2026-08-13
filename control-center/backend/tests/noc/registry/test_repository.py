"""Tests for the NodeRepository contract.

ENG-013B — Node SDK
"""

from __future__ import annotations

from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.registry.repository import NodeRepository


class FakeNodeRepository:
    """Minimal implementation used to verify repository substitutability."""

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
) -> Node:
    return Node(
        node_id=NodeId.create(
            id=node_id,
            name=node_id,
            display_name=node_id,
        ),
        node_type=NodeType.STREAMING,
    )


def test_fake_repository_satisfies_protocol() -> None:
    repository = FakeNodeRepository()

    assert isinstance(
        repository,
        NodeRepository,
    )


def test_repository_can_save_node() -> None:
    repository = FakeNodeRepository()
    node = make_node()

    repository.save(node)

    assert repository.count() == 1


def test_repository_can_get_node() -> None:
    repository = FakeNodeRepository()
    node = make_node()

    repository.save(node)

    result = repository.get(
        node.node_id
    )

    assert result is node


def test_repository_returns_none_for_unknown_node() -> None:
    repository = FakeNodeRepository()

    unknown = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    assert repository.get(
        unknown
    ) is None


def test_repository_exists() -> None:
    repository = FakeNodeRepository()
    node = make_node()

    assert repository.exists(
        node.node_id
    ) is False

    repository.save(node)

    assert repository.exists(
        node.node_id
    ) is True


def test_repository_save_replaces_same_identity() -> None:
    repository = FakeNodeRepository()

    first = make_node(
        "streaming-core"
    )

    second = Node(
        node_id=first.node_id,
        node_type=NodeType.STREAMING,
    )

    repository.save(first)
    repository.save(second)

    assert repository.count() == 1

    assert repository.get(
        first.node_id
    ) is second


def test_repository_lists_all_nodes() -> None:
    repository = FakeNodeRepository()

    first = make_node(
        "streaming-core"
    )

    second = make_node(
        "transcoding-core"
    )

    repository.save(first)
    repository.save(second)

    result = repository.list_all()

    assert isinstance(
        result,
        tuple,
    )

    assert len(result) == 2

    assert first in result
    assert second in result


def test_repository_delete_existing_node() -> None:
    repository = FakeNodeRepository()
    node = make_node()

    repository.save(node)

    removed = repository.delete(
        node.node_id
    )

    assert removed is True
    assert repository.count() == 0
    assert repository.get(
        node.node_id
    ) is None


def test_repository_delete_unknown_node() -> None:
    repository = FakeNodeRepository()

    unknown = NodeId.create(
        id="unknown-node",
        name="unknown",
        display_name="Unknown",
    )

    assert repository.delete(
        unknown
    ) is False


def test_repository_count_empty() -> None:
    repository = FakeNodeRepository()

    assert repository.count() == 0


def test_repository_count_multiple_nodes() -> None:
    repository = FakeNodeRepository()

    repository.save(
        make_node("node-a")
    )

    repository.save(
        make_node("node-b")
    )

    repository.save(
        make_node("node-c")
    )

    assert repository.count() == 3
