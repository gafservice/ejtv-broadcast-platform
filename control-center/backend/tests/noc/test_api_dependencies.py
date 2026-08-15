"""Tests for NOC runtime dependency composition."""

from app.api.dependencies import (
    get_alarm_service,
    get_heartbeat_service,
    get_metric_service,
    get_noc_repository,
    get_node_registry,
    get_snapshot_service,
)
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_service import AlarmService
from app.noc.services.heartbeat_service import HeartbeatService
from app.noc.services.metric_service import MetricService
from app.noc.services.snapshot_service import SnapshotService


def clear_noc_dependency_caches() -> None:
    """Reset all NOC dependency factories."""

    get_snapshot_service.cache_clear()
    get_alarm_service.cache_clear()
    get_metric_service.cache_clear()
    get_heartbeat_service.cache_clear()
    get_node_registry.cache_clear()
    get_noc_repository.cache_clear()


def setup_function() -> None:
    clear_noc_dependency_caches()


def teardown_function() -> None:
    clear_noc_dependency_caches()


def test_noc_repository_is_cached() -> None:
    first = get_noc_repository()
    second = get_noc_repository()

    assert first is second

    assert isinstance(
        first,
        InMemoryNodeRepository,
    )


def test_node_registry_is_cached() -> None:
    first = get_node_registry()
    second = get_node_registry()

    assert first is second

    assert isinstance(
        first,
        NodeRegistry,
    )


def test_registry_uses_shared_repository() -> None:
    repository = get_noc_repository()
    registry = get_node_registry()

    assert registry.repository is repository


def test_heartbeat_service_is_cached() -> None:
    first = get_heartbeat_service()
    second = get_heartbeat_service()

    assert first is second

    assert isinstance(
        first,
        HeartbeatService,
    )


def test_metric_service_is_cached() -> None:
    first = get_metric_service()
    second = get_metric_service()

    assert first is second

    assert isinstance(
        first,
        MetricService,
    )


def test_alarm_service_is_cached() -> None:
    first = get_alarm_service()
    second = get_alarm_service()

    assert first is second

    assert isinstance(
        first,
        AlarmService,
    )


def test_snapshot_service_is_cached() -> None:
    first = get_snapshot_service()
    second = get_snapshot_service()

    assert first is second

    assert isinstance(
        first,
        SnapshotService,
    )


def test_heartbeat_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_heartbeat_service().registry
        is registry
    )


def test_metric_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_metric_service().registry
        is registry
    )


def test_snapshot_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_snapshot_service().registry
        is registry
    )


def test_alarm_service_uses_shared_registry() -> None:
    registry = get_node_registry()

    assert (
        get_alarm_service()._registry
        is registry
    )


def test_all_services_share_same_registry() -> None:
    registry = get_node_registry()

    assert get_heartbeat_service().registry is registry
    assert get_metric_service().registry is registry
    assert get_alarm_service()._registry is registry
    assert get_snapshot_service().registry is registry


def test_repository_state_is_visible_through_registry() -> None:
    from app.noc.domain.node import Node
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_type import NodeType

    repository = get_noc_repository()
    registry = get_node_registry()

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    registry.register(node)

    assert repository.count() == 1

    assert repository.get(
        node.node_id
    ) is node


def test_registry_state_is_visible_to_services() -> None:
    from app.noc.domain.node import Node
    from app.noc.domain.node_id import NodeId
    from app.noc.domain.node_type import NodeType

    registry = get_node_registry()

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

    assert (
        get_heartbeat_service().is_present(
            node.node_id,
            instance.instance_id,
        )
        is False
    )

    assert (
        get_metric_service().current(
            node.node_id,
            instance.instance_id,
        ).samples
        == ()
    )

    assert (
        get_alarm_service().list_all(
            node.node_id,
            instance.instance_id,
        )
        == ()
    )
