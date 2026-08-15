"""Tests for NOC runtime bootstrap."""

import pytest

from app.noc.bootstrap import (
    DEFAULT_INSTANCE_ID,
    DEFAULT_NODE_DISPLAY_NAME,
    DEFAULT_NODE_ID,
    DEFAULT_NODE_NAME,
    NocBootstrapStatus,
    bootstrap_noc_runtime,
)
from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_type import NodeType
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.registry.registry import NodeRegistry


def make_registry() -> NodeRegistry:
    return NodeRegistry(
        InMemoryNodeRepository()
    )


def test_bootstrap_requires_registry() -> None:
    with pytest.raises(TypeError):
        bootstrap_noc_runtime(
            object()  # type: ignore[arg-type]
        )


def test_first_bootstrap_creates_node() -> None:
    registry = make_registry()

    result = bootstrap_noc_runtime(
        registry
    )

    assert result.status is NocBootstrapStatus.CREATED
    assert result.created is True
    assert result.changed is True
    assert registry.count() == 1


def test_created_node_has_canonical_identity() -> None:
    registry = make_registry()

    result = bootstrap_noc_runtime(
        registry
    )

    node = result.node

    assert node.node_id.id == DEFAULT_NODE_ID
    assert node.node_id.name == DEFAULT_NODE_NAME
    assert (
        node.node_id.display_name
        == DEFAULT_NODE_DISPLAY_NAME
    )
    assert node.node_type is NodeType.STREAMING


def test_created_node_has_primary_instance() -> None:
    registry = make_registry()

    node = bootstrap_noc_runtime(
        registry
    ).node

    assert node.instance_count == 1

    assert [
        str(instance.instance_id)
        for instance in node.instances
    ] == [
        DEFAULT_INSTANCE_ID
    ]


def test_bootstrap_does_not_invent_operational_state() -> None:
    registry = make_registry()

    node = bootstrap_noc_runtime(
        registry
    ).node

    instance = node.instances[0]

    assert instance.status is None
    assert instance.health is None
    assert instance.availability is None
    assert instance.heartbeat is None
    assert instance.metrics == ()
    assert instance.alarms == ()


def test_second_bootstrap_is_idempotent() -> None:
    registry = make_registry()

    first = bootstrap_noc_runtime(
        registry
    )

    second = bootstrap_noc_runtime(
        registry
    )

    assert first.status is NocBootstrapStatus.CREATED
    assert (
        second.status
        is NocBootstrapStatus.ALREADY_EXISTS
    )

    assert second.created is False
    assert second.changed is False
    assert registry.count() == 1
    assert second.node.instance_count == 1


def test_existing_node_without_instance_is_completed() -> None:
    registry = make_registry()

    node = Node(
        node_id=NodeId.create(
            id=DEFAULT_NODE_ID,
            name=DEFAULT_NODE_NAME,
            display_name=DEFAULT_NODE_DISPLAY_NAME,
        ),
        node_type=NodeType.STREAMING,
    )

    registry.register(node)

    result = bootstrap_noc_runtime(
        registry
    )

    assert (
        result.status
        is NocBootstrapStatus.INSTANCE_ADDED
    )

    assert result.changed is True
    assert result.node.instance_count == 1

    assert str(
        result.node.instances[0].instance_id
    ) == DEFAULT_INSTANCE_ID


def test_existing_node_type_conflict_is_rejected() -> None:
    registry = make_registry()

    node = Node(
        node_id=NodeId.create(
            id=DEFAULT_NODE_ID,
            name=DEFAULT_NODE_NAME,
            display_name=DEFAULT_NODE_DISPLAY_NAME,
        ),
        node_type=NodeType.TRANSCODING,
    )

    registry.register(node)

    with pytest.raises(RuntimeError):
        bootstrap_noc_runtime(
            registry
        )


def test_bootstrap_preserves_existing_instance_state() -> None:
    registry = make_registry()

    first = bootstrap_noc_runtime(
        registry
    )

    instance = first.node.instances[0]

    metrics_marker = object()
    instance.metrics = (
        metrics_marker,
    )

    second = bootstrap_noc_runtime(
        registry
    )

    assert (
        second.status
        is NocBootstrapStatus.ALREADY_EXISTS
    )

    assert second.node.instances[0] is instance
    assert instance.metrics == (
        metrics_marker,
    )


def test_runtime_info_requires_registry() -> None:
    from app.noc.bootstrap import (
        initialize_noc_runtime_info,
    )

    with pytest.raises(TypeError):
        initialize_noc_runtime_info(
            object()  # type: ignore[arg-type]
        )


def test_runtime_info_requires_bootstrapped_node() -> None:
    from app.noc.bootstrap import (
        initialize_noc_runtime_info,
    )

    registry = make_registry()

    with pytest.raises(RuntimeError):
        initialize_noc_runtime_info(
            registry
        )


def test_runtime_info_populates_node_info() -> None:
    from app.noc.bootstrap import (
        initialize_noc_runtime_info,
    )
    from app.noc.domain.node_info import NodeInfo

    registry = make_registry()

    node = bootstrap_noc_runtime(
        registry
    ).node

    instance = node.instances[0]

    assert instance.info is None

    initialize_noc_runtime_info(
        registry
    )

    assert isinstance(
        instance.info,
        NodeInfo,
    )

    assert (
        instance.info.instance_id
        == instance.instance_id
    )


def test_runtime_info_preserves_other_operational_state() -> None:
    from app.noc.bootstrap import (
        initialize_noc_runtime_info,
    )

    registry = make_registry()

    node = bootstrap_noc_runtime(
        registry
    ).node

    instance = node.instances[0]

    metrics_marker = object()
    alarms_marker = object()

    instance.metrics = (
        metrics_marker,
    )

    instance.alarms = (
        alarms_marker,
    )

    initialize_noc_runtime_info(
        registry
    )

    assert instance.metrics == (
        metrics_marker,
    )

    assert instance.alarms == (
        alarms_marker,
    )


def test_runtime_info_is_reflected_in_snapshot() -> None:
    from app.noc.bootstrap import (
        initialize_noc_runtime_info,
    )
    from app.noc.services.snapshot_service import (
        SnapshotService,
    )

    registry = make_registry()

    node = bootstrap_noc_runtime(
        registry
    ).node

    instance = node.instances[0]

    initialize_noc_runtime_info(
        registry
    )

    snapshot = SnapshotService(
        registry
    ).build(
        node.node_id,
        instance.instance_id,
    )

    assert snapshot.info is instance.info
    assert snapshot.info is not None
    assert (
        snapshot.info.instance_id
        == instance.instance_id
    )
