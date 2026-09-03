"""Tests for the operational NOC runtime ownership contract."""

from datetime import datetime, timezone

import pytest

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.runtime_owner import (
    RuntimeOwner,
    RuntimeOwnerIdentity,
)


def _node_id() -> NodeId:
    return NodeId(
        id="node-01",
        name="node-01",
        display_name="Node 01",
        created_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )


def test_runtime_owner_preserves_node_instance_identity() -> None:
    node_id = _node_id()
    instance_id = NodeInstanceId("instance-01")

    owner = RuntimeOwner(
        node_id=node_id,
        instance_id=instance_id,
    )

    assert owner.node_id == node_id
    assert owner.instance_id == instance_id
    assert owner.identity == RuntimeOwnerIdentity(
        node_id=node_id,
        instance_id=instance_id,
    )


def test_runtime_owner_identity_is_immutable() -> None:
    identity = RuntimeOwnerIdentity(
        node_id=_node_id(),
        instance_id=NodeInstanceId("instance-01"),
    )

    assert identity.node_id == _node_id()
    assert identity.instance_id == NodeInstanceId(
        "instance-01"
    )

    with pytest.raises(AttributeError):
        identity.instance_id = NodeInstanceId(  # type: ignore[misc]
            "instance-02"
        )
