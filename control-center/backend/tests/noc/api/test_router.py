"""HTTP integration tests for the NOC API."""

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_authorization_service,
    get_node_registry,
    get_snapshot_service,
)
from app.api.security import get_current_identity
from app.main import create_application
from app.noc.domain.node import Node
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_status import (
    NodeStatus,
    NodeStatusState,
)
from app.noc.domain.node_type import NodeType
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.services.snapshot_service import (
    SnapshotService,
)


class AllowAllAuthorizationService:
    """HTTP test double that accepts every authorization check."""

    def authorize(
        self,
        *,
        identity,
        permission,
    ) -> None:
        return None


def make_runtime():
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)
    snapshot_service = SnapshotService(
        registry
    )

    return (
        repository,
        registry,
        snapshot_service,
    )


def make_node() -> Node:
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

    instance.status = NodeStatus(
        NodeStatusState.RUNNING
    )

    instance.health = NodeHealth(
        NodeHealthState.HEALTHY
    )

    return node


def make_client(
    registry: NodeRegistry,
    snapshot_service: SnapshotService,
) -> TestClient:
    application = create_application()

    application.dependency_overrides[
        get_current_identity
    ] = lambda: object()

    application.dependency_overrides[
        get_authorization_service
    ] = lambda: AllowAllAuthorizationService()

    application.dependency_overrides[
        get_node_registry
    ] = lambda: registry

    application.dependency_overrides[
        get_snapshot_service
    ] = lambda: snapshot_service

    return TestClient(
        application
    )


def test_list_nodes_empty() -> None:
    _, registry, snapshots = make_runtime()

    client = make_client(
        registry,
        snapshots,
    )

    response = client.get(
        "/api/v1/noc/nodes"
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["nodes"] == []
    assert data["total"] == 0


def test_list_nodes() -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    client = make_client(
        registry,
        snapshots,
    )

    response = client.get(
        "/api/v1/noc/nodes"
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["total"] == 1

    assert data["nodes"][0][
        "node_id"
    ] == "streaming-core"

    assert data["nodes"][0][
        "node_type"
    ] == "STREAMING"

    assert data["nodes"][0][
        "instance_count"
    ] == 1


def test_get_node() -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    client = make_client(
        registry,
        snapshots,
    )

    response = client.get(
        "/api/v1/noc/nodes/streaming-core"
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["node_id"] == "streaming-core"
    assert data["name"] == "streaming"
    assert data["display_name"] == "Streaming Core"
    assert data["node_type"] == "STREAMING"


def test_get_unknown_node_returns_404() -> None:
    _, registry, snapshots = make_runtime()

    client = make_client(
        registry,
        snapshots,
    )

    response = client.get(
        "/api/v1/noc/nodes/unknown-node"
    )

    assert response.status_code == 404


def test_list_node_instances() -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()

    node.create_instance(
        instance_id="streaming-backup"
    )

    registry.register(node)

    client = make_client(
        registry,
        snapshots,
    )

    response = client.get(
        "/api/v1/noc/nodes/"
        "streaming-core/instances"
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["node_id"] == "streaming-core"
    assert data["total"] == 2

    assert {
        item["instance_id"]
        for item in data["instances"]
    } == {
        "streaming-primary",
        "streaming-backup",
    }


def test_list_instances_unknown_node_returns_404() -> None:
    _, registry, snapshots = make_runtime()

    client = make_client(
        registry,
        snapshots,
    )

    response = client.get(
        "/api/v1/noc/nodes/"
        "unknown-node/instances"
    )

    assert response.status_code == 404


def test_get_snapshot() -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    client = make_client(
        registry,
        snapshots,
    )

    response = client.get(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "streaming-primary/snapshot"
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["node_id"]["id"] == (
        "streaming-core"
    )

    assert data["node_type"] == (
        "STREAMING"
    )

    assert data["instance_id"] == (
        "streaming-primary"
    )

    assert data["status"]["state"] == (
        "RUNNING"
    )

    assert data["health"]["state"] == (
        "HEALTHY"
    )


def test_snapshot_unknown_node_returns_404() -> None:
    _, registry, snapshots = make_runtime()

    client = make_client(
        registry,
        snapshots,
    )

    response = client.get(
        "/api/v1/noc/nodes/"
        "unknown-node/instances/"
        "streaming-primary/snapshot"
    )

    assert response.status_code == 404


def test_snapshot_unknown_instance_returns_404() -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    client = make_client(
        registry,
        snapshots,
    )

    response = client.get(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "missing-instance/snapshot"
    )

    assert response.status_code == 404


def test_noc_requires_authentication() -> None:
    application = create_application()

    client = TestClient(
        application
    )

    response = client.get(
        "/api/v1/noc/nodes"
    )

    assert response.status_code == 401
