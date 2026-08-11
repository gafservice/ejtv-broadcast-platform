"""Tests for the Node Aggregate Root.

ENG-013B — Node SDK
NCS reference: 06-NODE.md
"""

import pytest

from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstance, NodeInstanceId
from app.noc.domain.node_type import NodeType


def make_node_id(
    identifier: str = "streaming-core",
) -> NodeId:
    return NodeId.create(
        id=identifier,
        name="streaming",
        display_name="Streaming Core",
    )


def make_node() -> Node:
    return Node(
        node_id=make_node_id(),
        node_type=NodeType.STREAMING,
    )


def test_node_can_be_created_without_instances() -> None:
    node = make_node()

    assert node.node_id.id == "streaming-core"
    assert node.node_type is NodeType.STREAMING
    assert node.instances == ()
    assert node.instance_count == 0


def test_node_rejects_invalid_node_id() -> None:
    with pytest.raises(TypeError):
        Node(
            node_id="streaming-core",  # type: ignore[arg-type]
            node_type=NodeType.STREAMING,
        )


def test_node_rejects_invalid_node_type() -> None:
    with pytest.raises(TypeError):
        Node(
            node_id=make_node_id(),
            node_type="STREAMING",  # type: ignore[arg-type]
        )


def test_node_adds_instance() -> None:
    node = make_node()

    instance = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=node.node_id,
    )

    node.add_instance(instance)

    assert node.instance_count == 1
    assert node.instances == (instance,)


def test_node_rejects_instance_from_different_node() -> None:
    node = make_node()

    other_node_id = make_node_id("other-streaming-node")

    instance = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=other_node_id,
    )

    with pytest.raises(ValueError):
        node.add_instance(instance)


def test_node_rejects_duplicate_instance_id() -> None:
    node = make_node()

    first = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=node.node_id,
    )

    duplicate = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=node.node_id,
    )

    node.add_instance(first)

    with pytest.raises(ValueError):
        node.add_instance(duplicate)


def test_node_create_instance_registers_instance() -> None:
    node = make_node()

    instance = node.create_instance(
        instance_id="streaming-primary",
    )

    assert instance.node_id == node.node_id
    assert instance.instance_id == NodeInstanceId(
        "streaming-primary"
    )
    assert node.instance_count == 1


def test_node_get_instance_by_string() -> None:
    node = make_node()

    instance = node.create_instance(
        instance_id="streaming-primary",
    )

    assert node.get_instance("streaming-primary") is instance


def test_node_get_instance_by_node_instance_id() -> None:
    node = make_node()

    instance = node.create_instance(
        instance_id="streaming-primary",
    )

    instance_id = NodeInstanceId("streaming-primary")

    assert node.get_instance(instance_id) is instance


def test_node_get_unknown_instance_returns_none() -> None:
    node = make_node()

    assert node.get_instance("missing") is None


def test_node_has_instance() -> None:
    node = make_node()

    node.create_instance(
        instance_id="streaming-primary",
    )

    assert node.has_instance("streaming-primary") is True
    assert node.has_instance("streaming-backup") is False


def test_node_contains_supports_instance_id() -> None:
    node = make_node()

    node.create_instance(
        instance_id="streaming-primary",
    )

    assert "streaming-primary" in node
    assert NodeInstanceId("streaming-primary") in node


def test_node_remove_instance() -> None:
    node = make_node()

    instance = node.create_instance(
        instance_id="streaming-primary",
    )

    removed = node.remove_instance(
        "streaming-primary"
    )

    assert removed is instance
    assert node.instance_count == 0
    assert node.instances == ()


def test_node_remove_unknown_instance_raises_key_error() -> None:
    node = make_node()

    with pytest.raises(KeyError):
        node.remove_instance("missing")


def test_node_remains_valid_without_instances() -> None:
    node = make_node()

    node.create_instance(
        instance_id="streaming-primary",
    )

    node.remove_instance(
        "streaming-primary"
    )

    assert node.node_id.id == "streaming-core"
    assert node.node_type is NodeType.STREAMING
    assert node.instance_count == 0


def test_node_instances_property_is_immutable_view() -> None:
    node = make_node()

    node.create_instance(
        instance_id="streaming-primary",
    )

    instances = node.instances

    assert isinstance(instances, tuple)


def test_node_len_returns_instance_count() -> None:
    node = make_node()

    node.create_instance(
        instance_id="streaming-primary",
    )
    node.create_instance(
        instance_id="streaming-backup",
    )

    assert len(node) == 2


def test_node_string_representation_is_node_id() -> None:
    node = make_node()

    assert str(node) == "streaming-core"


def test_node_rejects_invalid_instance_type() -> None:
    node = make_node()

    with pytest.raises(TypeError):
        node.add_instance(
            "streaming-primary"  # type: ignore[arg-type]
        )


def test_node_rejects_invalid_instance_lookup_type() -> None:
    node = make_node()

    with pytest.raises(TypeError):
        node.get_instance(123)  # type: ignore[arg-type]
