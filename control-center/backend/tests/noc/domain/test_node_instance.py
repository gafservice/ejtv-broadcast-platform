"""Tests for NodeInstance.

ENG-013B — Node SDK
NCS reference: 09-NODE-INSTANCE.md
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstance, NodeInstanceId


def make_node_id() -> NodeId:
    return NodeId.create(
        id="streaming-core",
        name="streaming",
        display_name="Streaming Core",
    )


def test_node_instance_id_can_be_created() -> None:
    instance_id = NodeInstanceId("streaming-primary")

    assert instance_id.value == "streaming-primary"


def test_node_instance_id_normalizes_whitespace() -> None:
    instance_id = NodeInstanceId("  streaming-primary  ")

    assert instance_id.value == "streaming-primary"


@pytest.mark.parametrize("value", ["", " ", "   "])
def test_node_instance_id_rejects_empty_values(value: str) -> None:
    with pytest.raises(ValueError):
        NodeInstanceId(value)


def test_node_instance_id_is_immutable() -> None:
    instance_id = NodeInstanceId("streaming-primary")

    with pytest.raises(AttributeError):
        instance_id.value = "streaming-backup"  # type: ignore[misc]


def test_node_instance_can_be_created() -> None:
    node_id = make_node_id()

    instance = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=node_id,
    )

    assert instance.instance_id == NodeInstanceId("streaming-primary")
    assert instance.node_id == node_id


def test_node_instance_create_uses_utc_time() -> None:
    instance = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=make_node_id(),
    )

    assert instance.created_at.tzinfo is not None
    assert instance.created_at.utcoffset() == timedelta(0)


def test_node_instance_accepts_explicit_utc_time() -> None:
    created_at = datetime(
        2026,
        8,
        11,
        19,
        0,
        tzinfo=timezone.utc,
    )

    instance = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=make_node_id(),
        created_at=created_at,
    )

    assert instance.created_at == created_at


def test_node_instance_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        NodeInstance(
            instance_id=NodeInstanceId("streaming-primary"),
            node_id=make_node_id(),
            created_at=datetime(2026, 8, 11, 19, 0),
        )


def test_node_instance_rejects_non_utc_datetime() -> None:
    non_utc = timezone(timedelta(hours=-6))

    with pytest.raises(ValueError):
        NodeInstance(
            instance_id=NodeInstanceId("streaming-primary"),
            node_id=make_node_id(),
            created_at=datetime(
                2026,
                8,
                11,
                13,
                0,
                tzinfo=non_utc,
            ),
        )


def test_node_instance_rejects_invalid_node_id_type() -> None:
    with pytest.raises(TypeError):
        NodeInstance(
            instance_id=NodeInstanceId("streaming-primary"),
            node_id="streaming-core",  # type: ignore[arg-type]
        )


def test_node_instance_rejects_invalid_instance_id_type() -> None:
    with pytest.raises(TypeError):
        NodeInstance(
            instance_id="streaming-primary",  # type: ignore[arg-type]
            node_id=make_node_id(),
        )


def test_node_instance_belongs_to_parent_node() -> None:
    node_id = make_node_id()

    instance = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=node_id,
    )

    assert instance.belongs_to(node_id) is True


def test_node_instance_does_not_belong_to_different_node() -> None:
    instance = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=make_node_id(),
    )

    other = NodeId.create(
        id="identity-core",
        name="identity",
        display_name="Identity Core",
    )

    assert instance.belongs_to(other) is False


def test_node_instance_operational_components_start_empty() -> None:
    instance = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=make_node_id(),
    )

    assert instance.info is None
    assert instance.status is None
    assert instance.health is None
    assert instance.availability is None
    assert instance.capabilities == ()
    assert instance.capacity is None
    assert instance.metrics == ()
    assert instance.events == ()
    assert instance.alarms == ()
    assert instance.heartbeat is None
    assert instance.snapshot is None


def test_node_instance_string_representation() -> None:
    instance = NodeInstance.create(
        instance_id="streaming-primary",
        node_id=make_node_id(),
    )

    assert str(instance) == "streaming-primary"
