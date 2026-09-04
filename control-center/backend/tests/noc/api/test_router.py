"""HTTP integration tests for the NOC API."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_authorization_service,
    get_history_csv_export_service,
    get_history_pdf_export_service,
    get_history_query_service,
    get_node_registry,
    get_snapshot_service,
)
from app.api.security import get_current_identity
from app.core.config import Settings, get_settings
from app.main import create_application
from app.noc.domain.node import Node
from app.noc.domain.node_alarm import (
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
)
from app.noc.history.csv_export_repository import (
    CsvExportResult,
)
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
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
from app.noc.services.history_query_service import (
    HistoryQueryResult,
)
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
    history_query_service=None,
    history_csv_export_service=None,
    history_pdf_export_service=None,
    settings=None,
) -> TestClient:
    application = create_application()

    if history_query_service is None:
        history_query_service = Mock()

    if history_csv_export_service is None:
        history_csv_export_service = Mock()

    if history_pdf_export_service is None:
        history_pdf_export_service = Mock()

    if settings is None:
        settings = Settings()

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

    application.dependency_overrides[
        get_history_query_service
    ] = lambda: history_query_service

    application.dependency_overrides[
        get_history_csv_export_service
    ] = lambda: history_csv_export_service

    application.dependency_overrides[
        get_history_pdf_export_service
    ] = lambda: history_pdf_export_service

    application.dependency_overrides[
        get_settings
    ] = lambda: settings

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


def test_get_last_24_hours_history() -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    instance = node.instances[0]

    history_query_service = Mock()

    start = datetime(
        2026,
        8,
        31,
        17,
        0,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2026,
        9,
        1,
        17,
        0,
        tzinfo=timezone.utc,
    )

    history_query_service.last_24_hours.return_value = (
        HistoryQueryResult(
            start=start,
            end=end,
            events=(),
            alarm_transitions=(),
        )
    )

    client = make_client(
        registry,
        snapshots,
        history_query_service,
    )

    response = client.get(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "streaming-primary/history/24h"
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["node_id"] == "streaming-core"
    assert data["instance_id"] == "streaming-primary"

    assert data["window"] == {
        "start": "2026-08-31T17:00:00Z",
        "end": "2026-09-01T17:00:00Z",
        "duration_hours": 24,
    }

    assert data["events"] == []
    assert data["alarm_transitions"] == []

    assert data["totals"] == {
        "events": 0,
        "alarm_transitions": 0,
    }

    history_query_service.last_24_hours.assert_called_once_with(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )


def test_history_unknown_node_returns_404() -> None:
    _, registry, snapshots = make_runtime()

    history_query_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_query_service,
    )

    response = client.get(
        "/api/v1/noc/nodes/"
        "unknown-node/instances/"
        "streaming-primary/history/24h"
    )

    assert response.status_code == 404

    history_query_service.last_24_hours.assert_not_called()


def test_history_unknown_instance_returns_404() -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    history_query_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_query_service,
    )

    response = client.get(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "missing-instance/history/24h"
    )

    assert response.status_code == 404

    history_query_service.last_24_hours.assert_not_called()


def test_history_serializes_event_and_alarm_transition() -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    instance = node.instances[0]

    event_time = datetime(
        2026,
        9,
        1,
        16,
        45,
        0,
        tzinfo=timezone.utc,
    )

    transition_time = datetime(
        2026,
        9,
        1,
        16,
        50,
        0,
        tzinfo=timezone.utc,
    )

    event = EventRecord(
        event_id="event-001",
        event_type="SESSION_CONNECTED",
        severity=EventSeverity.INFO,
        timestamp=event_time,
        source=instance.instance_id,
        title="SRT reader connected on ejtv",
        description="Reader session connected.",
        attributes={
            "path": "ejtv",
            "remote_address": "200.91.123.60:58816",
            "protocol": "SRT",
            "role": "READER",
        },
        correlation_id="corr-001",
    )

    event_history = EventHistoryRecord(
        event=event,
        node_id=node.node_id,
        instance_id=instance.instance_id,
        recorded_at=event_time,
    )

    transition = AlarmTransition(
        transition_id="alarm-transition-test-001",
        alarm_id="CRITICAL_PATH_TRAFFIC_STALLED:ejtv",
        transition_type=AlarmTransitionType.OPENED,
        timestamp=transition_time,
        source=instance.instance_id,
        state=AlarmState.ACTIVE,
        actor="noc-runtime",
        metadata={
            "path": "ejtv",
            "reason": "inbound bitrate is zero",
        },
    )

    history_query_service = Mock()

    history_query_service.last_24_hours.return_value = (
        HistoryQueryResult(
            start=datetime(
                2026,
                8,
                31,
                17,
                0,
                tzinfo=timezone.utc,
            ),
            end=datetime(
                2026,
                9,
                1,
                17,
                0,
                tzinfo=timezone.utc,
            ),
            events=(event_history,),
            alarm_transitions=(transition,),
        )
    )

    client = make_client(
        registry,
        snapshots,
        history_query_service,
    )

    response = client.get(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "streaming-primary/history/24h"
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["totals"] == {
        "events": 1,
        "alarm_transitions": 1,
    }

    assert data["events"] == [
        {
            "event_id": "event-001",
            "event_type": "SESSION_CONNECTED",
            "severity": "INFO",
            "timestamp": "2026-09-01T16:45:00Z",
            "source": "streaming-primary",
            "title": "SRT reader connected on ejtv",
            "description": "Reader session connected.",
            "attributes": {
                "path": "ejtv",
                "remote_address": "200.91.123.60:58816",
                "protocol": "SRT",
                "role": "READER",
            },
            "correlation_id": "corr-001",
            "recorded_at": "2026-09-01T16:45:00Z",
        }
    ]

    assert data["alarm_transitions"] == [
        {
            "transition_id": "alarm-transition-test-001",
            "alarm_id": (
                "CRITICAL_PATH_TRAFFIC_STALLED:ejtv"
            ),
            "transition_type": "OPENED",
            "timestamp": "2026-09-01T16:50:00Z",
            "source": "streaming-primary",
            "state": "ACTIVE",
            "actor": "noc-runtime",
            "metadata": {
                "path": "ejtv",
                "reason": "inbound bitrate is zero",
            },
        }
    ]


def test_csv_history_export_returns_public_metadata(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)
    instance = node.instances[0]

    export_service = Mock()

    export_service.export_range.return_value = CsvExportResult(
        path=tmp_path / "published",
        events_file=tmp_path / "published" / "events.csv",
        alarm_transitions_file=(
            tmp_path
            / "published"
            / "alarm_transitions.csv"
        ),
    )

    settings = Settings(
        noc_csv_export_path=str(tmp_path / "exports")
    )

    client = make_client(
        registry,
        snapshots,
        history_csv_export_service=export_service,
        settings=settings,
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "streaming-primary/history/exports/csv",
        json={
            "start": "2026-09-01T00:00:00Z",
            "end": "2026-09-02T00:00:00Z",
        },
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["format"] == "csv"
    assert data["node_id"] == "streaming-core"
    assert data["instance_id"] == "streaming-primary"

    assert data["window"] == {
        "start": "2026-09-01T00:00:00Z",
        "end": "2026-09-02T00:00:00Z",
    }

    assert data["files"] == [
        "events.csv",
        "alarm_transitions.csv",
    ]

    export_id = data["export_id"]

    assert len(export_id) == 32
    assert all(
        character in "0123456789abcdef"
        for character in export_id
    )

    call = export_service.export_range.call_args

    assert call.kwargs["start"] == datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )
    assert call.kwargs["end"] == datetime(
        2026,
        9,
        2,
        tzinfo=timezone.utc,
    )
    assert call.kwargs["node_id"] == node.node_id
    assert (
        call.kwargs["instance_id"]
        == instance.instance_id
    )

    destination = call.kwargs["destination"]

    assert destination.parent == tmp_path / "exports"
    assert destination.name == export_id

    assert "path" not in data
    assert str(tmp_path) not in response.text


def test_csv_history_export_unknown_node_returns_404(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    export_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_csv_export_service=export_service,
        settings=Settings(
            noc_csv_export_path=str(tmp_path / "exports")
        ),
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "unknown-node/instances/"
        "streaming-primary/history/exports/csv",
        json={
            "start": "2026-09-01T00:00:00Z",
            "end": "2026-09-02T00:00:00Z",
        },
    )

    assert response.status_code == 404
    export_service.export_range.assert_not_called()


def test_csv_history_export_unknown_instance_returns_404(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    export_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_csv_export_service=export_service,
        settings=Settings(
            noc_csv_export_path=str(tmp_path / "exports")
        ),
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "missing-instance/history/exports/csv",
        json={
            "start": "2026-09-01T00:00:00Z",
            "end": "2026-09-02T00:00:00Z",
        },
    )

    assert response.status_code == 404
    export_service.export_range.assert_not_called()


def test_csv_history_export_invalid_range_returns_422(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    export_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_csv_export_service=export_service,
        settings=Settings(
            noc_csv_export_path=str(tmp_path / "exports")
        ),
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "streaming-primary/history/exports/csv",
        json={
            "start": "2026-09-02T00:00:00Z",
            "end": "2026-09-01T00:00:00Z",
        },
    )

    assert response.status_code == 422
    export_service.export_range.assert_not_called()


def test_csv_history_export_rejects_client_filesystem_fields(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    export_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_csv_export_service=export_service,
        settings=Settings(
            noc_csv_export_path=str(tmp_path / "exports")
        ),
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "streaming-primary/history/exports/csv",
        json={
            "start": "2026-09-01T00:00:00Z",
            "end": "2026-09-02T00:00:00Z",
            "destination": "../../outside",
            "filename": "../../../secret.csv",
        },
    )

    assert response.status_code == 422
    export_service.export_range.assert_not_called()


def test_pdf_history_export_returns_public_metadata(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)
    instance = node.instances[0]

    export_service = Mock()

    from app.noc.history.pdf_export_repository import (
        PdfExportResult,
    )

    export_service.export_range.return_value = PdfExportResult(
        path=tmp_path / "published",
        report_file=(
            tmp_path
            / "published"
            / "history-report.pdf"
        ),
    )

    settings = Settings(
        noc_pdf_export_path=str(tmp_path / "exports")
    )

    client = make_client(
        registry,
        snapshots,
        history_pdf_export_service=export_service,
        settings=settings,
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "streaming-primary/history/exports/pdf",
        json={
            "start": "2026-09-01T00:00:00Z",
            "end": "2026-09-02T00:00:00Z",
        },
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["format"] == "pdf"
    assert data["node_id"] == "streaming-core"
    assert data["instance_id"] == "streaming-primary"

    assert data["window"] == {
        "start": "2026-09-01T00:00:00Z",
        "end": "2026-09-02T00:00:00Z",
    }

    assert data["files"] == [
        "history-report.pdf",
    ]

    export_id = data["export_id"]

    assert len(export_id) == 32
    assert all(
        character in "0123456789abcdef"
        for character in export_id
    )

    call = export_service.export_range.call_args

    assert call.kwargs["start"] == datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    assert call.kwargs["end"] == datetime(
        2026,
        9,
        2,
        tzinfo=timezone.utc,
    )

    assert call.kwargs["node_id"] == node.node_id
    assert (
        call.kwargs["instance_id"]
        == instance.instance_id
    )

    destination = call.kwargs["destination"]

    assert destination.parent == tmp_path / "exports"
    assert destination.name == export_id

    assert "path" not in data
    assert str(tmp_path) not in response.text


def test_pdf_history_export_unknown_node_returns_404(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    export_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_pdf_export_service=export_service,
        settings=Settings(
            noc_pdf_export_path=str(tmp_path / "exports")
        ),
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "unknown-node/instances/"
        "streaming-primary/history/exports/pdf",
        json={
            "start": "2026-09-01T00:00:00Z",
            "end": "2026-09-02T00:00:00Z",
        },
    )

    assert response.status_code == 404
    export_service.export_range.assert_not_called()


def test_pdf_history_export_unknown_instance_returns_404(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    export_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_pdf_export_service=export_service,
        settings=Settings(
            noc_pdf_export_path=str(tmp_path / "exports")
        ),
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "missing-instance/history/exports/pdf",
        json={
            "start": "2026-09-01T00:00:00Z",
            "end": "2026-09-02T00:00:00Z",
        },
    )

    assert response.status_code == 404
    export_service.export_range.assert_not_called()


def test_pdf_history_export_invalid_range_returns_422(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    export_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_pdf_export_service=export_service,
        settings=Settings(
            noc_pdf_export_path=str(tmp_path / "exports")
        ),
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "streaming-primary/history/exports/pdf",
        json={
            "start": "2026-09-02T00:00:00Z",
            "end": "2026-09-01T00:00:00Z",
        },
    )

    assert response.status_code == 422
    export_service.export_range.assert_not_called()


def test_pdf_history_export_rejects_client_filesystem_fields(
    tmp_path: Path,
) -> None:
    _, registry, snapshots = make_runtime()

    node = make_node()
    registry.register(node)

    export_service = Mock()

    client = make_client(
        registry,
        snapshots,
        history_pdf_export_service=export_service,
        settings=Settings(
            noc_pdf_export_path=str(tmp_path / "exports")
        ),
    )

    response = client.post(
        "/api/v1/noc/nodes/"
        "streaming-core/instances/"
        "streaming-primary/history/exports/pdf",
        json={
            "start": "2026-09-01T00:00:00Z",
            "end": "2026-09-02T00:00:00Z",
            "destination": "../../outside",
            "filename": "../../../secret.pdf",
        },
    )

    assert response.status_code == 422
    export_service.export_range.assert_not_called()
